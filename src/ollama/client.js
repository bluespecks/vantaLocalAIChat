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

export const chat = async (model, prompt, url = 'http://localhost:11434') => {
  try {
    const response = await fetch(`${url}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: prompt }],
        stream: false
      })
    });
    if (!response.ok) throw new Error(`HTTP error ${response.status}`);
    const data = await response.json();
    return data.message.content;
  } catch (error) {
    throw error;
  }
};
