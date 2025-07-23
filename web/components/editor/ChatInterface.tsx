import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { 
  MessageCircle, 
  Send, 
  Bot, 
  User, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  PlayCircle,
  Download,
  Loader2
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  operation?: {
    operation: string;
    parameters: any;
    confidence: number;
    explanation: string;
  };
  result?: {
    success: boolean;
    message: string;
    operation_id?: string;
    preview_url?: string;
    output_path?: string;
  };
}

interface ChatInterfaceProps {
  projectId: string;
  storyboardData?: any;
  onCommandExecuted?: (result: any) => void;
  className?: string;
}

export default function ChatInterface({ 
  projectId, 
  storyboardData, 
  onCommandExecuted,
  className = '' 
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi! I'm your AI video editor. I can help you edit your video using natural language commands. Try saying things like:\n\n• \"Cut the first 3 seconds of scene 2\"\n• \"Add fade transition between all scenes\"\n• \"Speed up scene 4 by 1.5x\"\n• \"Add text overlay 'THE END' to the last scene\"\n\nWhat would you like to do?",
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [suggestions] = useState([
    "Cut the first 3 seconds",
    "Add fade transition between scenes",
    "Speed up by 1.5x",
    "Add text overlay",
    "Reduce audio volume to 50%",
    "Add fade out at the end"
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isProcessing) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsProcessing(true);

    try {
      const response = await fetch('/api/editor/process-command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          command: userMessage.content,
          projectId,
          storyboardData
        }),
      });

      const result = await response.json();

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: result.message || 'Command processed',
        timestamp: new Date().toISOString(),
        operation: result.operation,
        result: result
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (onCommandExecuted) {
        onCommandExecuted(result);
      }

    } catch (error) {
      console.error('Error processing command:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing that command. Please try again.',
        timestamp: new Date().toISOString(),
        result: { success: false, message: 'Processing error' }
      };

      setMessages(prev => [...prev, errorMessage]);
    }

    setIsProcessing(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
    textareaRef.current?.focus();
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handlePreview = async (previewUrl: string) => {
    // Open preview in new window/modal
    window.open(previewUrl, '_blank');
  };

  const handleDownload = async (_outputPath: string, operationId: string) => {
    try {
      const response = await fetch(`/api/editor/download/${operationId}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `edited_video_${operationId}.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading video:', error);
    }
  };

  return (
    <Card className={`h-full flex flex-col bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader className="flex-shrink-0 border-b border-zinc-700">
        <CardTitle className="flex items-center gap-2 text-white">
          <MessageCircle className="w-5 h-5" />
          AI Video Editor Chat
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div className={`flex gap-3 max-w-[80%] ${
                message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}>
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user' 
                    ? 'bg-blue-600' 
                    : 'bg-green-600'
                }`}>
                  {message.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>

                {/* Message Content */}
                <div className={`flex flex-col gap-2 ${
                  message.role === 'user' ? 'items-end' : 'items-start'
                }`}>
                  {/* Message Bubble */}
                  <div className={`rounded-lg px-4 py-2 max-w-full ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-zinc-800 text-zinc-100 border border-zinc-700'
                  }`}>
                    <div className="whitespace-pre-wrap break-words">
                      {message.content}
                    </div>

                    {/* Operation Details */}
                    {message.operation && (
                      <div className="mt-2 p-2 bg-zinc-700 rounded text-sm">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className="text-xs">
                            {message.operation.operation}
                          </Badge>
                          <Badge 
                            variant={message.operation.confidence > 0.8 ? "default" : "secondary"}
                            className="text-xs"
                          >
                            {Math.round(message.operation.confidence * 100)}% confident
                          </Badge>
                        </div>
                        <p className="text-zinc-300">{message.operation.explanation}</p>
                      </div>
                    )}

                    {/* Result Actions */}
                    {message.result && message.result.success && (
                      <div className="mt-2 flex gap-2">
                        {message.result.preview_url && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handlePreview(message.result!.preview_url!)}
                            className="text-xs"
                          >
                            <PlayCircle className="w-3 h-3 mr-1" />
                            Preview
                          </Button>
                        )}
                        {message.result.operation_id && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDownload(
                              message.result!.output_path || '', 
                              message.result!.operation_id!
                            )}
                            className="text-xs"
                          >
                            <Download className="w-3 h-3 mr-1" />
                            Download
                          </Button>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Timestamp and Status */}
                  <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <Clock className="w-3 h-3" />
                    {formatTimestamp(message.timestamp)}
                    
                    {message.result && (
                      <>
                        {message.result.success ? (
                          <CheckCircle className="w-3 h-3 text-green-500" />
                        ) : (
                          <AlertCircle className="w-3 h-3 text-red-500" />
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {isProcessing && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="flex items-center gap-2 text-zinc-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing your command...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {messages.length <= 1 && (
          <div className="p-4 border-t border-zinc-700">
            <p className="text-sm text-zinc-400 mb-2">Quick suggestions:</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs bg-zinc-800 border-zinc-600 hover:bg-zinc-700"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="flex-shrink-0 p-4 border-t border-zinc-700">
          <div className="flex gap-2">
            <Textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Tell me what you'd like to do with your video..."
              className="flex-1 min-h-[2.5rem] max-h-32 resize-none bg-zinc-800 border-zinc-600 text-white placeholder-zinc-400"
              disabled={isProcessing}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isProcessing}
              className="px-3 bg-blue-600 hover:bg-blue-700"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}