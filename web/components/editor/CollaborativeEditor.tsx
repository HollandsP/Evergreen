import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Avatar } from '../ui/avatar';
import { 
  Users,
  MessageCircle,
  Send,
  User,
  MousePointer,
  Edit3,
  Eye,
  Shield,
  Settings,
  Lock,
  Unlock,
  UserPlus,
  UserMinus,
  Share2,
  Link,
  Copy,
  Check,
  Bell,
  BellOff,
  Circle,
  Square,
  Type,
  Hand,
  Navigation,
  Mic,
  MicOff,
  Video,
  VideoOff,
  Screen,
  ScreenShare,
  ChevronDown,
  ChevronUp,
  Clock,
  Activity,
  AlertCircle,
  Info
} from 'lucide-react';

interface Collaborator {
  id: string;
  name: string;
  email?: string;
  avatar?: string;
  color: string;
  role: 'owner' | 'editor' | 'viewer' | 'commenter';
  status: 'online' | 'away' | 'offline';
  lastActive?: Date;
  cursor?: { x: number; y: number };
  selection?: { start: number; end: number };
  currentOperation?: string;
  permissions?: {
    canEdit: boolean;
    canComment: boolean;
    canShare: boolean;
    canDelete: boolean;
  };
}

interface Comment {
  id: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  timestamp: Date;
  message: string;
  resolved?: boolean;
  replies?: Comment[];
  position?: { time: number; clipId?: string };
}

interface Activity {
  id: string;
  userId: string;
  userName: string;
  action: string;
  target?: string;
  timestamp: Date;
  details?: any;
}

interface CollaborativeEditorProps {
  projectId: string;
  currentUserId: string;
  onInviteUser?: (email: string, role: Collaborator['role']) => void;
  onRemoveUser?: (userId: string) => void;
  onChangeRole?: (userId: string, role: Collaborator['role']) => void;
  onSendComment?: (comment: Omit<Comment, 'id' | 'timestamp'>) => void;
  className?: string;
}

// Predefined colors for collaborators
const COLLABORATOR_COLORS = [
  '#3B82F6', // blue
  '#10B981', // green
  '#F59E0B', // yellow
  '#EF4444', // red
  '#8B5CF6', // purple
  '#EC4899', // pink
  '#06B6D4', // cyan
  '#F97316', // orange
];

// Role permissions
const ROLE_PERMISSIONS = {
  owner: { canEdit: true, canComment: true, canShare: true, canDelete: true },
  editor: { canEdit: true, canComment: true, canShare: true, canDelete: false },
  commenter: { canEdit: false, canComment: true, canShare: false, canDelete: false },
  viewer: { canEdit: false, canComment: false, canShare: false, canDelete: false }
};

export default function CollaborativeEditor({ 
  projectId,
  currentUserId,
  onInviteUser,
  onRemoveUser,
  onChangeRole,
  onSendComment,
  className = '' 
}: CollaborativeEditorProps) {
  // State management
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [currentUser, setCurrentUser] = useState<Collaborator | null>(null);
  const [showChat, setShowChat] = useState(true);
  const [showActivity, setShowActivity] = useState(false);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<Collaborator['role']>('viewer');
  const [chatMessage, setChatMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  const [notifications, setNotifications] = useState(true);
  const [shareLink, setShareLink] = useState('');
  const [linkCopied, setLinkCopied] = useState(false);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  
  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const typingTimeoutRef = useRef<NodeJS.Timeout>();

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [projectId]);

  // Generate share link
  useEffect(() => {
    setShareLink(`${window.location.origin}/edit/${projectId}?invite=true`);
  }, [projectId]);

  const connectWebSocket = () => {
    try {
      // In production, this would connect to your WebSocket server
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001';
      wsRef.current = new WebSocket(`${wsUrl}/collaboration/${projectId}`);

      wsRef.current.onopen = () => {
        console.log('Collaborative editing connected');
        // Send user info
        sendWebSocketMessage({
          type: 'join',
          userId: currentUserId,
          projectId
        });
      };

      wsRef.current.onmessage = (event) => {
        handleWebSocketMessage(JSON.parse(event.data));
      };

      wsRef.current.onclose = () => {
        console.log('Collaborative editing disconnected');
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      // For demo purposes, initialize with mock data
      initializeMockData();
    }
  };

  const sendWebSocketMessage = (message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'collaborators':
        setCollaborators(message.data);
        const user = message.data.find((c: Collaborator) => c.id === currentUserId);
        if (user) setCurrentUser(user);
        break;
        
      case 'user-joined':
        addActivity({
          userId: message.userId,
          userName: message.userName,
          action: 'joined the project'
        });
        break;
        
      case 'user-left':
        setCollaborators(prev => prev.map(c => 
          c.id === message.userId ? { ...c, status: 'offline' as const } : c
        ));
        addActivity({
          userId: message.userId,
          userName: message.userName,
          action: 'left the project'
        });
        break;
        
      case 'cursor-update':
        setCollaborators(prev => prev.map(c => 
          c.id === message.userId ? { ...c, cursor: message.cursor } : c
        ));
        break;
        
      case 'selection-update':
        setCollaborators(prev => prev.map(c => 
          c.id === message.userId ? { ...c, selection: message.selection } : c
        ));
        break;
        
      case 'operation-update':
        setCollaborators(prev => prev.map(c => 
          c.id === message.userId ? { ...c, currentOperation: message.operation } : c
        ));
        addActivity({
          userId: message.userId,
          userName: message.userName,
          action: message.operation,
          target: message.target
        });
        break;
        
      case 'comment':
        setComments(prev => [...prev, message.comment]);
        if (notifications && message.userId !== currentUserId) {
          // Show notification
        }
        break;
        
      case 'typing-start':
        setTypingUsers(prev => new Set(prev).add(message.userId));
        break;
        
      case 'typing-stop':
        setTypingUsers(prev => {
          const newSet = new Set(prev);
          newSet.delete(message.userId);
          return newSet;
        });
        break;
    }
  };

  // Initialize with mock data for demo
  const initializeMockData = () => {
    const mockCollaborators: Collaborator[] = [
      {
        id: currentUserId,
        name: 'You',
        email: 'you@example.com',
        color: COLLABORATOR_COLORS[0],
        role: 'owner',
        status: 'online',
        permissions: ROLE_PERMISSIONS.owner
      },
      {
        id: 'user2',
        name: 'Sarah Chen',
        email: 'sarah@example.com',
        avatar: 'https://i.pravatar.cc/150?u=sarah',
        color: COLLABORATOR_COLORS[1],
        role: 'editor',
        status: 'online',
        lastActive: new Date(),
        cursor: { x: 450, y: 200 },
        currentOperation: 'Adding transitions',
        permissions: ROLE_PERMISSIONS.editor
      },
      {
        id: 'user3',
        name: 'Mike Johnson',
        email: 'mike@example.com',
        avatar: 'https://i.pravatar.cc/150?u=mike',
        color: COLLABORATOR_COLORS[2],
        role: 'editor',
        status: 'away',
        lastActive: new Date(Date.now() - 10 * 60 * 1000),
        permissions: ROLE_PERMISSIONS.editor
      },
      {
        id: 'user4',
        name: 'Emma Wilson',
        email: 'emma@example.com',
        avatar: 'https://i.pravatar.cc/150?u=emma',
        color: COLLABORATOR_COLORS[3],
        role: 'commenter',
        status: 'online',
        lastActive: new Date(),
        permissions: ROLE_PERMISSIONS.commenter
      }
    ];

    const mockComments: Comment[] = [
      {
        id: '1',
        userId: 'user2',
        userName: 'Sarah Chen',
        userAvatar: 'https://i.pravatar.cc/150?u=sarah',
        timestamp: new Date(Date.now() - 30 * 60 * 1000),
        message: 'Love the intro animation! Maybe we could make it a bit faster?',
        position: { time: 2.5 }
      },
      {
        id: '2',
        userId: 'user4',
        userName: 'Emma Wilson',
        userAvatar: 'https://i.pravatar.cc/150?u=emma',
        timestamp: new Date(Date.now() - 15 * 60 * 1000),
        message: 'The audio levels seem a bit low in scene 3',
        position: { time: 45, clipId: 'scene-3' }
      }
    ];

    const mockActivities: Activity[] = [
      {
        id: '1',
        userId: 'user2',
        userName: 'Sarah Chen',
        action: 'added fade transition',
        target: 'between Scene 1 and Scene 2',
        timestamp: new Date(Date.now() - 5 * 60 * 1000)
      },
      {
        id: '2',
        userId: 'user3',
        userName: 'Mike Johnson',
        action: 'adjusted audio levels',
        target: 'Scene 3',
        timestamp: new Date(Date.now() - 12 * 60 * 1000)
      }
    ];

    setCollaborators(mockCollaborators);
    setCurrentUser(mockCollaborators[0]);
    setComments(mockComments);
    setActivities(mockActivities);
  };

  // Add activity helper
  const addActivity = (activity: Omit<Activity, 'id' | 'timestamp'>) => {
    const newActivity: Activity = {
      ...activity,
      id: Date.now().toString(),
      timestamp: new Date()
    };
    setActivities(prev => [newActivity, ...prev].slice(0, 50)); // Keep last 50 activities
  };

  // Handle chat message
  const handleSendMessage = () => {
    if (!chatMessage.trim()) return;

    const comment: Comment = {
      id: Date.now().toString(),
      userId: currentUserId,
      userName: currentUser?.name || 'Unknown',
      userAvatar: currentUser?.avatar,
      timestamp: new Date(),
      message: chatMessage
    };

    // Send via WebSocket
    sendWebSocketMessage({
      type: 'comment',
      comment,
      userId: currentUserId
    });

    // Add locally
    setComments(prev => [...prev, comment]);
    setChatMessage('');

    if (onSendComment) {
      onSendComment(comment);
    }
  };

  // Handle typing indicator
  const handleTyping = () => {
    if (!isTyping) {
      setIsTyping(true);
      sendWebSocketMessage({
        type: 'typing-start',
        userId: currentUserId
      });
    }

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set new timeout
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      sendWebSocketMessage({
        type: 'typing-stop',
        userId: currentUserId
      });
    }, 1000);
  };

  // Handle invite
  const handleInvite = () => {
    if (!inviteEmail || !onInviteUser) return;

    onInviteUser(inviteEmail, inviteRole);
    setInviteEmail('');
    setShowInvite(false);

    // Add activity
    addActivity({
      userId: currentUserId,
      userName: currentUser?.name || 'Unknown',
      action: `invited ${inviteEmail}`,
      details: { role: inviteRole }
    });
  };

  // Handle share link copy
  const handleCopyLink = () => {
    navigator.clipboard.writeText(shareLink);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  // Format time ago
  const formatTimeAgo = (date: Date) => {
    const minutes = Math.floor((Date.now() - date.getTime()) / 60000);
    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  // Get role badge color
  const getRoleBadgeColor = (role: Collaborator['role']) => {
    switch (role) {
      case 'owner': return 'bg-purple-600';
      case 'editor': return 'bg-blue-600';
      case 'commenter': return 'bg-green-600';
      case 'viewer': return 'bg-zinc-600';
      default: return 'bg-zinc-600';
    }
  };

  // Get status color
  const getStatusColor = (status: Collaborator['status']) => {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'away': return 'bg-yellow-500';
      case 'offline': return 'bg-zinc-500';
      default: return 'bg-zinc-500';
    }
  };

  return (
    <Card className={`h-full flex flex-col bg-zinc-900 border-zinc-700 ${className}`}>
      <CardHeader className="flex-shrink-0 border-b border-zinc-700">
        <CardTitle className="flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Collaborative Editing
            <Badge variant="outline" className="text-xs">
              {collaborators.filter(c => c.status === 'online').length} online
            </Badge>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Voice/Video controls */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsVoiceEnabled(!isVoiceEnabled)}
              className={isVoiceEnabled ? 'text-green-400' : 'text-zinc-400'}
            >
              {isVoiceEnabled ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsVideoEnabled(!isVideoEnabled)}
              className={isVideoEnabled ? 'text-green-400' : 'text-zinc-400'}
            >
              {isVideoEnabled ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsScreenSharing(!isScreenSharing)}
              className={isScreenSharing ? 'text-blue-400' : 'text-zinc-400'}
            >
              {isScreenSharing ? <ScreenShare className="w-4 h-4" /> : <Screen className="w-4 h-4" />}
            </Button>
            
            <div className="w-px h-6 bg-zinc-700" />
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setNotifications(!notifications)}
              className={notifications ? 'text-blue-400' : 'text-zinc-400'}
            >
              {notifications ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowInvite(!showInvite)}
              className="text-zinc-400"
            >
              <UserPlus className="w-4 h-4" />
            </Button>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Invite Panel */}
        {showInvite && (
          <div className="p-4 border-b border-zinc-700 bg-zinc-950">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-white">Invite Collaborators</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowInvite(false)}
                className="h-6 w-6 p-0"
              >
                <ChevronUp className="w-4 h-4" />
              </Button>
            </div>
            
            <div className="space-y-3">
              <div className="flex gap-2">
                <Input
                  placeholder="Email address"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="flex-1 bg-zinc-800 border-zinc-600 text-white"
                />
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as Collaborator['role'])}
                  className="bg-zinc-800 border border-zinc-600 text-white px-3 py-2 rounded-md"
                >
                  <option value="viewer">Viewer</option>
                  <option value="commenter">Commenter</option>
                  <option value="editor">Editor</option>
                </select>
                <Button
                  onClick={handleInvite}
                  disabled={!inviteEmail}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Invite
                </Button>
              </div>
              
              <div className="flex items-center gap-2 p-2 bg-zinc-800 rounded">
                <Link className="w-4 h-4 text-zinc-400" />
                <input
                  value={shareLink}
                  readOnly
                  className="flex-1 bg-transparent text-zinc-300 text-sm outline-none"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopyLink}
                  className="text-xs"
                >
                  {linkCopied ? (
                    <>
                      <Check className="w-3 h-3 mr-1" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3 mr-1" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 flex">
          {/* Collaborators List */}
          <div className="w-64 border-r border-zinc-700 flex flex-col">
            <div className="p-3 border-b border-zinc-700">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-zinc-300">Team</h3>
                <Badge variant="secondary" className="text-xs">
                  {collaborators.length} members
                </Badge>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {collaborators.map(collaborator => (
                <div
                  key={collaborator.id}
                  className="flex items-center justify-between p-2 rounded hover:bg-zinc-800 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      {collaborator.avatar ? (
                        <img
                          src={collaborator.avatar}
                          alt={collaborator.name}
                          className="w-8 h-8 rounded-full"
                        />
                      ) : (
                        <div 
                          className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                          style={{ backgroundColor: collaborator.color }}
                        >
                          {collaborator.name.charAt(0).toUpperCase()}
                        </div>
                      )}
                      <div 
                        className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-zinc-900 ${
                          getStatusColor(collaborator.status)
                        }`}
                      />
                    </div>
                    
                    <div>
                      <div className="flex items-center gap-1">
                        <span className="text-sm text-white">
                          {collaborator.name}
                          {collaborator.id === currentUserId && ' (You)'}
                        </span>
                      </div>
                      {collaborator.currentOperation && (
                        <p className="text-xs text-zinc-400 truncate">
                          {collaborator.currentOperation}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <Badge 
                    variant="secondary" 
                    className={`text-xs ${getRoleBadgeColor(collaborator.role)} text-white`}
                  >
                    {collaborator.role}
                  </Badge>
                </div>
              ))}
            </div>
          </div>

          {/* Chat/Activity Panel */}
          <div className="flex-1 flex flex-col">
            <div className="flex border-b border-zinc-700">
              <Button
                variant={showChat ? 'default' : 'ghost'}
                size="sm"
                onClick={() => {
                  setShowChat(true);
                  setShowActivity(false);
                }}
                className="flex-1 rounded-none"
              >
                <MessageCircle className="w-4 h-4 mr-1" />
                Chat
                {comments.length > 0 && (
                  <Badge variant="secondary" className="ml-2 text-xs">
                    {comments.length}
                  </Badge>
                )}
              </Button>
              <Button
                variant={showActivity ? 'default' : 'ghost'}
                size="sm"
                onClick={() => {
                  setShowChat(false);
                  setShowActivity(true);
                }}
                className="flex-1 rounded-none"
              >
                <Activity className="w-4 h-4 mr-1" />
                Activity
              </Button>
            </div>

            {/* Chat View */}
            {showChat && (
              <>
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {comments.map(comment => (
                    <div key={comment.id} className="flex gap-3">
                      {comment.userAvatar ? (
                        <img
                          src={comment.userAvatar}
                          alt={comment.userName}
                          className="w-8 h-8 rounded-full flex-shrink-0"
                        />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center flex-shrink-0">
                          <User className="w-4 h-4 text-zinc-400" />
                        </div>
                      )}
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-white">
                            {comment.userName}
                          </span>
                          <span className="text-xs text-zinc-500">
                            {formatTimeAgo(comment.timestamp)}
                          </span>
                          {comment.position && (
                            <Badge variant="outline" className="text-xs">
                              {comment.position.clipId || formatTime(comment.position.time)}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-zinc-300">{comment.message}</p>
                      </div>
                    </div>
                  ))}
                  
                  {typingUsers.size > 0 && (
                    <div className="flex items-center gap-2 text-sm text-zinc-400">
                      <div className="flex gap-1">
                        <Circle className="w-2 h-2 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <Circle className="w-2 h-2 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <Circle className="w-2 h-2 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                      <span>
                        {Array.from(typingUsers).map(userId => 
                          collaborators.find(c => c.id === userId)?.name
                        ).filter(Boolean).join(', ')} typing...
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="border-t border-zinc-700 p-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Type a message..."
                      value={chatMessage}
                      onChange={(e) => {
                        setChatMessage(e.target.value);
                        handleTyping();
                      }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      className="flex-1 bg-zinc-800 border-zinc-600 text-white"
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={!chatMessage.trim()}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </>
            )}

            {/* Activity View */}
            {showActivity && (
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {activities.map(activity => (
                  <div key={activity.id} className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center flex-shrink-0">
                      <Edit3 className="w-4 h-4 text-zinc-400" />
                    </div>
                    
                    <div className="flex-1">
                      <p className="text-sm text-zinc-300">
                        <span className="font-medium text-white">{activity.userName}</span>
                        {' '}{activity.action}
                        {activity.target && (
                          <span className="text-zinc-400"> {activity.target}</span>
                        )}
                      </p>
                      <p className="text-xs text-zinc-500 mt-1">
                        {formatTimeAgo(activity.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
                
                {activities.length === 0 && (
                  <div className="text-center text-zinc-500 py-8">
                    <Activity className="w-8 h-8 mx-auto mb-2" />
                    <p className="text-sm">No recent activity</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Cursor Overlay (would be rendered over the main editing area) */}
        {collaborators.filter(c => c.cursor && c.id !== currentUserId).map(collaborator => (
          <div
            key={collaborator.id}
            className="absolute pointer-events-none"
            style={{
              left: collaborator.cursor?.x,
              top: collaborator.cursor?.y,
              color: collaborator.color
            }}
          >
            <MousePointer className="w-4 h-4" fill={collaborator.color} />
            <span className="absolute left-5 top-0 text-xs bg-zinc-800 text-white px-1 rounded">
              {collaborator.name}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// Helper function for time formatting
function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}