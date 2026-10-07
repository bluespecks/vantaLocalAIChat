import React, { useState, useEffect } from 'react';
import { render, Text, Box, useInput, useApp } from 'ink';
import { checkOllama, getModels, streamChat } from './ollama/client.js';

function App() {
  const [status, setStatus] = useState('checking');
  const [models, setModels] = useState([]);
  const [modelIndex, setModelIndex] = useState(0);
  const [selectedModel, setSelectedModel] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const { exit } = useApp();

  useEffect(() => {
    async function init() {
      const isConnected = await checkOllama();
      if (!isConnected) {
        setStatus('disconnected');
        return;
      }
      setStatus('connected');
      const modelList = await getModels();
      setModels(modelList);
    }
    init();
  }, []);

  const handleSend = async (userQuery) => {
    setPrompt('');
    setMessages(prev => [
      ...prev,
      { sender: 'user', text: userQuery },
      { sender: 'assistant', text: '', model: selectedModel }
    ]);
    setLoading(true);

    try {
      for await (const chunk of streamChat(selectedModel, userQuery)) {
        setMessages(prev => {
          const next = [...prev];
          const last = { ...next[next.length - 1] };
          last.text += chunk;
          next[next.length - 1] = last;
          return next;
        });
      }
    } catch (err) {
      setMessages(prev => {
        const next = [...prev];
        const last = { ...next[next.length - 1] };
        last.text += `\n[Error: ${err.message}]`;
        next[next.length - 1] = last;
        return next;
      });
    } finally {
      setLoading(false);
    }
  };

  useInput((input, key) => {
    if (input === 'c' && key.ctrl) {
      exit();
      return;
    }

    if (!selectedModel) {
      if (key.upArrow) setModelIndex(prev => (prev - 1 + models.length) % models.length);
      else if (key.downArrow) setModelIndex(prev => (prev + 1) % models.length);
      else if (key.return) if (models.length > 0) setSelectedModel(models[modelIndex]);
      return;
    }

    if (loading) return;

    if (key.return) {
      if (prompt.trim().length === 0) return;
      handleSend(prompt);
    } else if (key.backspace || key.delete) {
      setPrompt(prev => prev.slice(0, -1));
    } else if (input && !key.ctrl && !key.meta) {
      setPrompt(prev => prev + input);
    }
  });

  return (
    <Box flexDirection="column">
      <Text bold>Vanta — Phase 2B (Streaming Cleanup)</Text>
      <Text color="gray" dimColor>Ctrl+C to exit</Text>
      <Box marginTop={1}>
        <Text>Ollama: </Text>
        {status === 'checking' && <Text color="yellow">Checking...</Text>}
        {status === 'connected' && <Text color="green">● Connected</Text>}
        {status === 'disconnected' && (
          <Box flexDirection="column">
            <Text color="red">✗ Not reachable</Text>
            <Text color="gray">Please start Ollama and try again.</Text>
          </Box>
        )}
      </Box>

      {status === 'connected' && (
        <>
          {!selectedModel ? (
            <Box flexDirection="column" marginTop={1}>
              <Text bold>Available models:</Text>
              {models.length === 0 ? (
                <Text color="gray">No models installed.</Text>
              ) : (
                models.map((m, i) => (
                  <Text key={m} color={i === modelIndex ? 'cyan' : undefined}>
                    {i === modelIndex ? `> ${m}` : `  ${m}`}
                  </Text>
                ))
              )}
              <Box marginTop={1}>
                <Text color="gray">Use ↑/↓ to navigate, Enter to select.</Text>
              </Box>
            </Box>
          ) : (
            <Box flexDirection="column" marginTop={1}>
              <Text bold>Selected: {selectedModel}</Text>

              {messages.map((m, i) => (
                <Box key={i} flexDirection="column" marginTop={1}>
                  <Text bold>{m.sender === 'user' ? 'User:' : `Assistant · ${m.model || selectedModel}:`}</Text>
                  <Text>{m.text}</Text>
                </Box>
              ))}

              {loading && (
                <Box marginTop={1}>
                  <Text color="gray">⠋ Generating...</Text>
                </Box>
              )}

              {!loading && (
                <Box flexDirection="column" marginTop={1}>
                  <Text bold>User:</Text>
                  <Text>{prompt || <Text color="gray">_</Text>}</Text>
                </Box>
              )}
            </Box>
          )}
        </>
      )}
    </Box>
  );
}

render(<App />);
