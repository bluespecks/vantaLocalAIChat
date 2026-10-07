import React, { useState, useEffect } from 'react';
import { render, Text, Box, useInput, useApp } from 'ink';
import { checkOllama, getModels, chat } from './ollama/client.js';

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

  useInput(async (input, key) => {
    // Ctrl+C exit
    if (input === 'c' && key.ctrl) {
      exit();
      return;
    }

    // Model selection mode
    if (!selectedModel) {
      if (key.upArrow) {
        setModelIndex(prev => (prev - 1 + models.length) % models.length);
      } else if (key.downArrow) {
        setModelIndex(prev => (prev + 1) % models.length);
      } else if (key.return || input === '\r' || input === '\n') {
        if (models.length > 0) setSelectedModel(models[modelIndex]);
      }
      return;
    }

    // Chat input mode
    if (loading) return;

    if (key.return || input === '\r' || input === '\n') {
      if (prompt.trim().length === 0) return;
      const userQuery = prompt;
      setPrompt('');
      setMessages(prev => [...prev, { sender: 'user', text: userQuery }]);
      setLoading(true);

      try {
        const responseData = await chat(selectedModel, userQuery);
        setMessages(prev => [...prev, { sender: 'assistant', text: responseData }]);
      } catch (err) {
        setMessages(prev => [...prev, { sender: 'assistant', text: `Error: ${err.message}` }]);
      } finally {
        setLoading(false);
      }
    } else if (key.backspace || key.delete) {
      setPrompt(prev => prev.slice(0, -1));
    } else if (input && !key.ctrl && !key.meta) {
      if (input.includes('\r') || input.includes('\n')) {
        const clean = input.replace(/[\r\n]/g, '');
        const fullPrompt = (prompt + clean).trim();
        if (fullPrompt.length > 0) {
          setPrompt('');
          setMessages(prev => [...prev, { sender: 'user', text: fullPrompt }]);
          setLoading(true);
          try {
            const responseData = await chat(selectedModel, fullPrompt);
            setMessages(prev => [...prev, { sender: 'assistant', text: responseData }]);
          } catch (err) {
            setMessages(prev => [...prev, { sender: 'assistant', text: `Error: ${err.message}` }]);
          } finally {
            setLoading(false);
          }
        }
      } else {
        setPrompt(prev => prev + input);
      }
    }
  });

  return (
    <Box flexDirection="column">
      <Text bold>Vanta — Phase 1</Text>
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
                  <Text bold>{m.sender === 'user' ? 'User:' : 'Assistant:'}</Text>
                  <Text>{m.text}</Text>
                </Box>
              ))}

              <Box flexDirection="column" marginTop={1}>
                <Text bold>User:</Text>
                <Text>{loading ? 'Thinking...' : (prompt || <Text color="gray">_</Text>)}</Text>
              </Box>
            </Box>
          )}
        </>
      )}
    </Box>
  );
}

render(<App />);
