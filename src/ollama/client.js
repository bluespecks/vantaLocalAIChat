export const checkOllama = async (url = 'http://localhost:11434') => {
  try {
    const response = await fetch(`${url}/api/tags`);
    return response.ok;
  } catch {
    return false;
  }
};

export const getModels = async (url = 'http://localhost:11434') => {
  try {
    const response = await fetch(`${url}/api/tags`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.models.map(m => m.name);
  } catch {
    return [];
  }
};

export async function* streamChat(model, prompt, url = 'http://localhost:11434') {
  const response = await fetch(`${url}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: prompt }],
      stream: true
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }

  // Debug: Is this a stream?
  // console.error("Is stream?", response.body && typeof response.body.getReader === 'function');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    let lines = buffer.split('\n');
    buffer = lines.pop(); // last chunk

    for (const line of lines) {
      if (line.trim() === '') continue;
      try {
        const chunk = JSON.parse(line);
        if (chunk.message?.content) {
          yield chunk.message.content;
        }
        if (chunk.done) return;
      } catch (err) {
        throw new Error('Malformed JSON chunk');
      }
    }
  }
}
