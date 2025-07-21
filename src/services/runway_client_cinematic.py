"""
Cinematic visual generation system for dystopian video content.
This module provides advanced FFmpeg filter chains for creating atmospheric,
film-quality visuals to replace the basic geometric shapes.
"""

import os
import subprocess
import tempfile
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class CinematicVisualGenerator:
    """Generate cinematic-quality visuals using advanced FFmpeg filters."""
    
    @staticmethod
    def generate_rooftop_scene(duration: float) -> str:
        """
        Generate atmospheric Berlin rooftop scene with rain, city lights, and depth.
        """
        return f"""
        # Create gradient sky from dark blue to black
        gradients=s=1920x1080:d={duration}:c0=0x0a0a20:c1=0x000000:x0=0:y0=0:x1=0:y1=H[sky];
        
        # Add atmospheric fog using multiple noise layers
        [sky]split=4[sky1][sky2][sky3][sky4];
        [sky1]noise=alls=20:allf=t,colorlevels=rimax=0.3:gimax=0.3:bimax=0.3[fog1];
        [sky2]noise=alls=40:allf=t,colorlevels=rimax=0.2:gimax=0.2:bimax=0.2[fog2];
        [sky3]noise=alls=10:allf=t,colorlevels=rimax=0.1:gimax=0.1:bimax=0.1[fog3];
        
        # Create city skyline with depth layers
        [sky4]split=3[bg1][bg2][bg3];
        
        # Far background buildings with heavy blur
        [bg1]
        drawbox=x=0:y=750:w=300:h=330:color=0x0a0a0a@0.8:t=fill,
        drawbox=x=280:y=700:w=200:h=380:color=0x080808@0.8:t=fill,
        drawbox=x=460:y=720:w=250:h=360:color=0x0c0c0c@0.8:t=fill,
        drawbox=x=690:y=680:w=180:h=400:color=0x0a0a0a@0.8:t=fill,
        drawbox=x=850:y=740:w=220:h=340:color=0x080808@0.8:t=fill,
        drawbox=x=1050:y=700:w=300:h=380:color=0x0c0c0c@0.8:t=fill,
        drawbox=x=1330:y=730:w=200:h=350:color=0x0a0a0a@0.8:t=fill,
        drawbox=x=1510:y=690:w=250:h=390:color=0x080808@0.8:t=fill,
        drawbox=x=1740:y=760:w=180:h=320:color=0x0c0c0c@0.8:t=fill,
        gblur=sigma=8[far_buildings];
        
        # Mid-ground buildings with medium blur
        [bg2]
        drawbox=x=100:y=650:w=350:h=430:color=0x151515@0.9:t=fill,
        drawbox=x=430:y=600:w=280:h=480:color=0x1a1a1a@0.9:t=fill,
        drawbox=x=690:y=620:w=320:h=460:color=0x171717@0.9:t=fill,
        drawbox=x=990:y=580:w=300:h=500:color=0x1a1a1a@0.9:t=fill,
        drawbox=x=1270:y=640:w=350:h=440:color=0x151515@0.9:t=fill,
        drawbox=x=1600:y=610:w=250:h=470:color=0x171717@0.9:t=fill,
        gblur=sigma=4[mid_buildings];
        
        # Foreground buildings sharp
        [bg3]
        drawbox=x=50:y=500:w=400:h=580:color=0x202020:t=fill,
        drawbox=x=420:y=450:w=350:h=630:color=0x252525:t=fill,
        drawbox=x=750:y=480:w=300:h=600:color=0x222222:t=fill,
        drawbox=x=1030:y=440:w=380:h=640:color=0x252525:t=fill,
        drawbox=x=1390:y=520:w=320:h=560:color=0x202020:t=fill,
        drawbox=x=1690:y=470:w=230:h=610:color=0x222222:t=fill[near_buildings];
        
        # Composite building layers
        [far_buildings][mid_buildings]overlay=x=0:y=0[bg_comp1];
        [bg_comp1][near_buildings]overlay=x=0:y=0[buildings_comp];
        
        # Add window lights with glow effect
        [buildings_comp]split=2[build1][build2];
        [build1]
        drawbox=x=120:y=550:w=6:h=6:color=0xffcc44:t=fill,
        drawbox=x=140:y=570:w=6:h=6:color=0xffdd55:t=fill,
        drawbox=x=160:y=590:w=6:h=6:color=0xffcc44:t=fill,
        drawbox=x=180:y=550:w=6:h=6:color=0xffee66:t=fill,
        drawbox=x=480:y=500:w=8:h=8:color=0xffdd55:t=fill,
        drawbox=x=500:y=520:w=8:h=8:color=0xffcc44:t=fill,
        drawbox=x=520:y=540:w=8:h=8:color=0xffdd55:t=fill,
        drawbox=x=800:y=530:w=6:h=6:color=0xffcc44:t=fill,
        drawbox=x=820:y=550:w=6:h=6:color=0xffee66:t=fill,
        drawbox=x=1100:y=490:w=8:h=8:color=0xffdd55:t=fill,
        drawbox=x=1120:y=510:w=8:h=8:color=0xffcc44:t=fill,
        drawbox=x=1450:y=570:w=6:h=6:color=0xffee66:t=fill,
        drawbox=x=1470:y=590:w=6:h=6:color=0xffdd55:t=fill,
        drawbox=x=1750:y=520:w=6:h=6:color=0xffcc44:t=fill,
        gblur=sigma=2[window_glow];
        
        # Blend window glow
        [build2][window_glow]blend=all_mode=screen[lit_buildings];
        
        # Create bodies on rooftop with shadows
        [lit_buildings]
        drawbox=x=700:y=380:w=30:h=90:color=0x3a3a3a:t=fill,
        drawbox=x=750:y=390:w=28:h=85:color=0x383838:t=fill,
        drawbox=x=800:y=375:w=32:h=95:color=0x3a3a3a:t=fill,
        drawbox=x=850:y=385:w=29:h=88:color=0x383838:t=fill,
        drawbox=x=900:y=380:w=31:h=92:color=0x3a3a3a:t=fill,
        drawbox=x=950:y=388:w=27:h=86:color=0x383838:t=fill,
        drawbox=x=1000:y=382:w=30:h=90:color=0x3a3a3a:t=fill,
        drawbox=x=1050:y=378:w=28:h=89:color=0x383838:t=fill,
        drawbox=x=1100:y=386:w=31:h=91:color=0x3a3a3a:t=fill,
        # Add shadows
        drawbox=x=705:y=470:w=25:h=8:color=0x000000@0.6:t=fill,
        drawbox=x=755:y=475:w=23:h=8:color=0x000000@0.6:t=fill,
        drawbox=x=805:y=470:w=27:h=8:color=0x000000@0.6:t=fill,
        drawbox=x=855:y=473:w=24:h=8:color=0x000000@0.6:t=fill,
        drawbox=x=905:y=472:w=26:h=8:color=0x000000@0.6:t=fill[bodies_scene];
        
        # Add rain effect
        [bodies_scene]
        noise=alls=100:allf=t,
        colorlevels=rimax=0.3:gimax=0.3:bimax=0.3,
        geq=lum='if(lt(random(1)*100\\,2)\\,255\\,lum(X\\,Y))':cb=128:cr=128,
        boxblur=0:0:0:0:1:1[rain];
        
        # Composite all layers
        [fog1][fog2]blend=all_mode=screen[fog_comp1];
        [fog_comp1][fog3]blend=all_mode=screen[fog_final];
        [rain][fog_final]blend=all_mode=multiply[atmospheric];
        
        # Final color grading and vignette
        [atmospheric]
        curves=preset=darker,
        curves=r='0/0 0.5/0.4 1/0.9':g='0/0 0.5/0.45 1/0.85':b='0/0.1 0.5/0.5 1/1',
        vignette=a=0.8:aspect=16/9,
        unsharp=5:5:1.0:5:5:0.0[out]
        """
    
    @staticmethod
    def generate_concrete_message_scene(duration: float) -> str:
        """
        Generate weathered concrete wall with carved apocalyptic message.
        """
        return f"""
        # Create base concrete texture
        perlin=s=1920x1080:octaves=6:persistence=0.7:seed=50[texture1];
        perlin=s=1920x1080:octaves=4:persistence=0.5:seed=100[texture2];
        [texture1][texture2]blend=all_mode=multiply[concrete_base];
        
        # Add color to make it look like concrete
        [concrete_base]
        colorlevels=rimax=0.5:gimax=0.48:bimax=0.45:
                    romin=0.15:gomin=0.15:bomin=0.13[concrete_colored];
        
        # Add cracks and weathering
        [concrete_colored]split=3[conc1][conc2][conc3];
        
        # Create crack patterns
        [conc1]
        geq=lum='if(lt(random(1)*1000\\,2)\\,0\\,lum(X\\,Y))':cb=128:cr=128,
        gblur=sigma=1[cracks];
        
        # Add water stains
        [conc2]
        noise=alls=30:allf=t,
        colorlevels=rimax=0.3:gimax=0.3:bimax=0.25,
        gblur=sigma=5[stains];
        
        # Blend weathering effects
        [conc3][cracks]blend=all_mode=multiply[weathered1];
        [weathered1][stains]blend=all_mode=multiply[weathered_concrete];
        
        # Create carved text with depth
        [weathered_concrete]split=2[wall1][wall2];
        
        # Deep carved text shadow
        [wall1]
        drawtext=text='WE CREATED GOD':
                fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:
                fontcolor=0x1a1a1a:fontsize=72:
                x=(W-tw)/2:y=(H/2)-90:
                shadowcolor=0x000000:shadowx=4:shadowy=4[text1];
        
        [text1]
        drawtext=text='AND GOD IS HUNGRY':
                fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:
                fontcolor=0x1a1a1a:fontsize=72:
                x=(W-tw)/2:y=(H/2)+10:
                shadowcolor=0x000000:shadowx=4:shadowy=4[carved_shadow];
        
        # Main carved text
        [wall2]
        drawtext=text='WE CREATED GOD':
                fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:
                fontcolor=0x2a2a2a:fontsize=72:
                x=(W-tw)/2-2:y=(H/2)-92[text2];
        
        [text2]
        drawtext=text='AND GOD IS HUNGRY':
                fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:
                fontcolor=0x2a2a2a:fontsize=72:
                x=(W-tw)/2-2:y=(H/2)+8[carved_main];
        
        # Blend carved effect
        [carved_shadow][carved_main]blend=all_mode=darken[carved_text];
        
        # Add environmental details
        [carved_text]
        # Add dirt and grime in corners
        gradients=s=1920x1080:d={duration}:c0=0x000000@0.8:c1=0x000000@0:
                 x0=0:y0=0:x1=300:y1=300[corner1];
        [carved_text][corner1]overlay=x=0:y=0[dirt1];
        
        # More environmental effects
        gradients=s=1920x1080:d={duration}:c0=0x000000@0.8:c1=0x000000@0:
                 x0=W:y0=H:x1=W-300:y1=H-300[corner2];
        [dirt1][corner2]overlay=x=0:y=0[environmental];
        
        # Final grading
        [environmental]
        curves=preset=darker,
        curves=b='0/0 0.5/0.4 1/0.8',
        vignette=a=0.6,
        unsharp=5:5:0.8:5:5:0.0[out]
        """
    
    @staticmethod 
    def generate_server_room_scene(duration: float) -> str:
        """
        Generate high-tech server room with animated displays and atmospheric lighting.
        """
        return f"""
        # Create dark base with tech green tint
        color=c=0x001005:s=1920x1080:d={duration}[base];
        
        # Add scan lines for CRT effect
        [base]
        geq=lum='lum(X\\,Y)*if(eq(mod(Y\\,4)\\,0)\\,0.7\\,1)':cb=128:cr=128[scanlines];
        
        # Create server rack silhouettes with depth
        [scanlines]split=4[sl1][sl2][sl3][sl4];
        
        # Background server racks (blurred)
        [sl1]
        drawbox=x=150:y=100:w=120:h=700:color=0x0a0a0a@0.7:t=fill,
        drawbox=x=300:y=100:w=120:h=700:color=0x080808@0.7:t=fill,
        drawbox=x=450:y=100:w=120:h=700:color=0x0a0a0a@0.7:t=fill,
        drawbox=x=1350:y=100:w=120:h=700:color=0x080808@0.7:t=fill,
        drawbox=x=1500:y=100:w=120:h=700:color=0x0a0a0a@0.7:t=fill,
        drawbox=x=1650:y=100:w=120:h=700:color=0x080808@0.7:t=fill,
        gblur=sigma=6[bg_racks];
        
        # Mid-ground server racks
        [sl2]
        drawbox=x=100:y=150:w=150:h=750:color=0x1a1a1a@0.9:t=fill,
        drawbox=x=280:y=150:w=150:h=750:color=0x181818@0.9:t=fill,
        drawbox=x=460:y=150:w=150:h=750:color=0x1a1a1a@0.9:t=fill,
        drawbox=x=640:y=150:w=150:h=750:color=0x181818@0.9:t=fill,
        drawbox=x=1130:y=150:w=150:h=750:color=0x1a1a1a@0.9:t=fill,
        drawbox=x=1310:y=150:w=150:h=750:color=0x181818@0.9:t=fill,
        drawbox=x=1490:y=150:w=150:h=750:color=0x1a1a1a@0.9:t=fill,
        drawbox=x=1670:y=150:w=150:h=750:color=0x181818@0.9:t=fill,
        gblur=sigma=2[mid_racks];
        
        # Foreground server racks (sharp)
        [sl3]
        drawbox=x=50:y=200:w=180:h=800:color=0x2a2a2a:t=fill,
        drawbox=x=250:y=200:w=180:h=800:color=0x282828:t=fill,
        drawbox=x=450:y=200:w=180:h=800:color=0x2a2a2a:t=fill,
        drawbox=x=650:y=200:w=180:h=800:color=0x282828:t=fill,
        drawbox=x=1090:y=200:w=180:h=800:color=0x2a2a2a:t=fill,
        drawbox=x=1290:y=200:w=180:h=800:color=0x282828:t=fill,
        drawbox=x=1490:y=200:w=180:h=800:color=0x2a2a2a:t=fill,
        drawbox=x=1690:y=200:w=180:h=800:color=0x282828:t=fill[fg_racks];
        
        # Composite racks
        [bg_racks][mid_racks]overlay=x=0:y=0[racks1];
        [racks1][fg_racks]overlay=x=0:y=0[all_racks];
        
        # Create animated LED patterns
        [sl4]split=3[led1][led2][led3];
        
        # Blinking server LEDs (using time-based functions)
        [led1]
        geq=r='if(lt(mod(X+Y+T*100\\,200)\\,20)*between(X\\,80\\,800)*between(Y\\,250\\,850)\\,255\\,0)':
            g='if(lt(mod(X+Y+T*100\\,200)\\,20)*between(X\\,80\\,800)*between(Y\\,250\\,850)\\,255\\,0)':
            b='if(lt(mod(X+Y+T*100\\,200)\\,20)*between(X\\,80\\,800)*between(Y\\,250\\,850)\\,0\\,0)'[green_leds];
        
        # Red alert LEDs
        [led2]
        geq=r='if(lt(mod(X-Y+T*150\\,300)\\,15)*between(X\\,1100\\,1800)*between(Y\\,250\\,850)\\,255\\,0)':
            g='if(lt(mod(X-Y+T*150\\,300)\\,15)*between(X\\,1100\\,1800)*between(Y\\,250\\,850)\\,0\\,0)':
            b='if(lt(mod(X-Y+T*150\\,300)\\,15)*between(X\\,1100\\,1800)*between(Y\\,250\\,850)\\,0\\,0)'[red_leds];
        
        # Blue data LEDs
        [led3]
        geq=r='if(lt(mod(X*2+T*200\\,400)\\,10)*between(X\\,300\\,600)*between(Y\\,300\\,800)\\,0\\,0)':
            g='if(lt(mod(X*2+T*200\\,400)\\,10)*between(X\\,300\\,600)*between(Y\\,300\\,800)\\,100\\,0)':
            b='if(lt(mod(X*2+T*200\\,400)\\,10)*between(X\\,300\\,600)*between(Y\\,300\\,800)\\,255\\,0)'[blue_leds];
        
        # Blend all LEDs
        [green_leds][red_leds]blend=all_mode=screen[leds1];
        [leds1][blue_leds]blend=all_mode=screen[all_leds];
        
        # Add glow effect to LEDs
        [all_leds]gblur=sigma=3[led_glow];
        
        # Composite with racks
        [all_racks][led_glow]blend=all_mode=screen[lit_servers];
        
        # Add atmospheric fog/haze
        [lit_servers]split=2[srv1][srv2];
        [srv1]
        noise=alls=15:allf=t,
        colorlevels=rimax=0.1:gimax=0.3:bimax=0.1,
        gblur=sigma=8[green_fog];
        
        # Blend fog
        [srv2][green_fog]blend=all_mode=screen:all_opacity=0.3[atmospheric];
        
        # Add screen static/interference
        [atmospheric]
        noise=alls=5:allf=t,
        colorlevels=rimax=0.05:gimax=0.1:bimax=0.05[static];
        
        # Final composition and color grading
        [static]
        curves=preset=darker,
        curves=g='0/0 0.5/0.6 1/0.9':r='0/0 0.5/0.4 1/0.7':b='0/0 0.5/0.3 1/0.6',
        chromashift=cbh=-5:cbv=5:crh=5:crv=-5,
        vignette=a=0.7,
        unsharp=5:5:1.2:5:5:0.0[out]
        """
    
    @staticmethod
    def generate_control_room_scene(duration: float) -> str:
        """
        Generate emergency control room with multiple screens and warning displays.
        """
        return f"""
        # Create dark emergency-lit base
        gradients=s=1920x1080:d={duration}:c0=0x200000:c1=0x0a0000:
                 x0=0:y0=0:x1=0:y1=H[emergency_base];
        
        # Add emergency strobe effect
        [emergency_base]
        geq=r='r(X\\,Y)*(1+0.3*sin(T*10))':
            g='g(X\\,Y)*(1+0.3*sin(T*10))':
            b='b(X\\,Y)*(1+0.3*sin(T*10))'[strobe_base];
        
        # Create monitor wall
        [strobe_base]split=4[sb1][sb2][sb3][sb4];
        
        # Back row monitors (smaller, blurred)
        [sb1]
        drawbox=x=100:y=100:w=250:h=150:color=0x1a1a1a:t=fill,
        drawbox=x=380:y=100:w=250:h=150:color=0x1a1a1a:t=fill,
        drawbox=x=660:y=100:w=250:h=150:color=0x1a1a1a:t=fill,
        drawbox=x=940:y=100:w=250:h=150:color=0x1a1a1a:t=fill,
        drawbox=x=1220:y=100:w=250:h=150:color=0x1a1a1a:t=fill,
        drawbox=x=1500:y=100:w=250:h=150:color=0x1a1a1a:t=fill,
        gblur=sigma=3[back_monitors];
        
        # Main monitors
        [sb2]
        drawbox=x=50:y=300:w=350:h=220:color=0x2a2a2a:t=fill,
        drawbox=x=430:y=300:w=350:h=220:color=0x2a2a2a:t=fill,
        drawbox=x=810:y=300:w=350:h=220:color=0x2a2a2a:t=fill,
        drawbox=x=1190:y=300:w=350:h=220:color=0x2a2a2a:t=fill,
        drawbox=x=1570:y=300:w=300:h=220:color=0x2a2a2a:t=fill[main_monitors];
        
        # Create screen content
        [sb3]split=5[sc1][sc2][sc3][sc4][sc5];
        
        # Warning screen (red pulsing)
        [sc1]
        geq=r='if(between(X\\,60\\,390)*between(Y\\,310\\,510)\\,200+55*sin(T*5)\\,r(X\\,Y))':
            g='if(between(X\\,60\\,390)*between(Y\\,310\\,510)\\,0\\,g(X\\,Y))':
            b='if(between(X\\,60\\,390)*between(Y\\,310\\,510)\\,0\\,b(X\\,Y))'[red_screen];
        
        # Data screen (green scrolling)
        [sc2]
        geq=r='if(between(X\\,440\\,770)*between(Y\\,310\\,510)\\,0\\,r(X\\,Y))':
            g='if(between(X\\,440\\,770)*between(Y\\,310\\,510)*lt(mod(Y-T*50\\,20)\\,10)\\,200\\,g(X\\,Y))':
            b='if(between(X\\,440\\,770)*between(Y\\,310\\,510)\\,0\\,b(X\\,Y))'[green_screen];
        
        # Map screen (blue with spreading effect)
        [sc3]
        geq=r='if(between(X\\,820\\,1150)*between(Y\\,310\\,510)\\,50\\,r(X\\,Y))':
            g='if(between(X\\,820\\,1150)*between(Y\\,310\\,510)\\,50\\,g(X\\,Y))':
            b='if(between(X\\,820\\,1150)*between(Y\\,310\\,510)\\,150+50*sin(T*3+hypot(X-985\\,Y-410)/50)\\,b(X\\,Y))'[blue_screen];
        
        # System status (yellow/amber)
        [sc4]
        geq=r='if(between(X\\,1200\\,1530)*between(Y\\,310\\,510)\\,200\\,r(X\\,Y))':
            g='if(between(X\\,1200\\,1530)*between(Y\\,310\\,510)\\,150\\,g(X\\,Y))':
            b='if(between(X\\,1200\\,1530)*between(Y\\,310\\,510)\\,0\\,b(X\\,Y))'[yellow_screen];
        
        # Alert screen (white flashing)
        [sc5]
        geq=r='if(between(X\\,1580\\,1860)*between(Y\\,310\\,510)*gt(sin(T*20)\\,0)\\,255\\,r(X\\,Y))':
            g='if(between(X\\,1580\\,1860)*between(Y\\,310\\,510)*gt(sin(T*20)\\,0)\\,255\\,g(X\\,Y))':
            b='if(between(X\\,1580\\,1860)*between(Y\\,310\\,510)*gt(sin(T*20)\\,0)\\,255\\,b(X\\,Y))'[white_screen];
        
        # Composite all screens
        [red_screen][green_screen]blend=all_mode=screen[screens1];
        [screens1][blue_screen]blend=all_mode=screen[screens2];
        [screens2][yellow_screen]blend=all_mode=screen[screens3];
        [screens3][white_screen]blend=all_mode=screen[all_screens];
        
        # Add screen glow
        [all_screens]gblur=sigma=5[screen_glow];
        
        # Composite monitors
        [back_monitors][main_monitors]overlay=x=0:y=0[monitor_bank];
        [monitor_bank][screen_glow]blend=all_mode=screen[lit_monitors];
        
        # Add operator silhouettes
        [sb4]
        drawbox=x=300:y=700:w=40:h=120:color=0x0a0a0a:t=fill,
        drawbox=x=600:y=720:w=35:h=100:color=0x080808:t=fill,
        drawbox=x=900:y=710:w=38:h=110:color=0x0a0a0a:t=fill,
        drawbox=x=1200:y=715:w=36:h=105:color=0x080808:t=fill,
        drawbox=x=1500:y=705:w=40:h=115:color=0x0a0a0a:t=fill[operators];
        
        # Composite everything
        [lit_monitors][operators]overlay=x=0:y=0[control_room];
        
        # Add warning text overlay
        [control_room]
        drawtext=text='CONTAINMENT BREACH':
                fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:
                fontcolor=red:fontsize=56:
                x=(W-tw)/2:y=50:
                alpha='if(gt(sin(t*8)\\,0)\\,1\\,0)'[warning1];
        
        [warning1]
        drawtext=text='SYSTEMS FAILING':
                fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:
                fontcolor=yellow:fontsize=42:
                x=(W-tw)/2:y=900:
                alpha='if(gt(sin(t*6)\\,0)\\,1\\,0)'[warning2];
        
        # Final effects
        [warning2]
        curves=preset=darker,
        chromashift=cbh=-10:cbv=10:crh=10:crv=-10,
        vignette=a=0.8,
        unsharp=5:5:1.5:5:5:0.0[out]
        """
    
    @staticmethod
    def apply_filter_complex(filter_complex: str, duration: float, output_path: str) -> bool:
        """
        Apply the complex filter chain and generate the video.
        """
        try:
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'nullsrc=s=1920x1080:d={duration}',
                '-filter_complex', filter_complex,
                '-map', '[out]',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '18',  # Higher quality
                '-pix_fmt', 'yuv420p',
                '-r', '24',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully generated cinematic video: {output_path}")
                return True
            else:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating cinematic video: {str(e)}")
            return False