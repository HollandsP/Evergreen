import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';
import { Slider } from '../ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Mic, User, Sparkles, Volume2 } from 'lucide-react';

interface LipSyncControlsProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  speaker?: string;
}

export default function LipSyncControls({ enabled, onToggle, speaker }: LipSyncControlsProps) {
  const [performanceLevel, setPerformanceLevel] = React.useState('natural');
  const [expressiveness, setExpressiveness] = React.useState(70);
  const [audioSensitivity, setAudioSensitivity] = React.useState(50);

  return (
    <Card>
      <CardContent className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mic className="w-4 h-4 text-muted-foreground" />
            <Label htmlFor="lip-sync">Audio-Driven Lip Sync</Label>
          </div>
          <Switch
            id="lip-sync"
            checked={enabled}
            onCheckedChange={onToggle}
          />
        </div>

        {enabled && (
          <>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <User className="w-4 h-4 text-muted-foreground" />
                <span className="text-muted-foreground">Speaking Character:</span>
                <span className="font-medium">{speaker || 'Unknown'}</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="performance">Performance Style</Label>
              <Select value={performanceLevel} onValueChange={setPerformanceLevel}>
                <SelectTrigger id="performance">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="subtle">
                    <div className="flex items-center gap-2">
                      <span>Subtle</span>
                      <span className="text-xs text-muted-foreground">Minimal movement</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="natural">
                    <div className="flex items-center gap-2">
                      <span>Natural</span>
                      <span className="text-xs text-muted-foreground">Realistic speech</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="expressive">
                    <div className="flex items-center gap-2">
                      <span>Expressive</span>
                      <span className="text-xs text-muted-foreground">Animated delivery</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="theatrical">
                    <div className="flex items-center gap-2">
                      <span>Theatrical</span>
                      <span className="text-xs text-muted-foreground">Dramatic performance</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="expressiveness" className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Facial Expressiveness
                </Label>
                <span className="text-sm text-muted-foreground">{expressiveness}%</span>
              </div>
              <Slider
                id="expressiveness"
                value={[expressiveness]}
                onValueChange={([value]) => setExpressiveness(value)}
                max={100}
                step={10}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="sensitivity" className="flex items-center gap-2">
                  <Volume2 className="w-4 h-4" />
                  Audio Sensitivity
                </Label>
                <span className="text-sm text-muted-foreground">{audioSensitivity}%</span>
              </div>
              <Slider
                id="sensitivity"
                value={[audioSensitivity]}
                onValueChange={([value]) => setAudioSensitivity(value)}
                max={100}
                step={10}
                className="w-full"
              />
            </div>

            <div className="bg-muted/50 p-3 rounded-lg">
              <p className="text-xs text-muted-foreground">
                Lip sync will automatically match mouth movements to the audio track. 
                Higher expressiveness adds more facial animations and gestures.
              </p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
