# 
# My setup consists of:
#
#  CH Combatstick USB
#   Map zoom toggle button #3 into FOV axis w/two positions (long press for Freetrack Reset)
#   Map push button #3 into Teamspeak PTT
#  Saitek Thottle Quadrant
#   Split 2nd Axis into 2 Buttons (Speedbrake Extend/Retract)
#   Split 3rd Axis into 2 Buttons (Gear Up/Down)
#  Phidget Encoder 1
#   Map Push Button into Button
#   Map Rotation into Axis (Radar Elevation)
#  Phidget Encoder 2
#   Map Push Button into Button (Missile Uncage)
#   Map Rotation into Axis (Missile Acquisition Sound Level)
#
import joysticks, phidgets, state, log, keyboard, falcon, time

vjoy = joysticks.get('vJoy Device')
combatstick = joysticks.get("CH Combatstick USB")
pedals = joysticks.get('CH Pro Pedals USB')
throttle = joysticks.get('Saitek Pro Flight Quadrant')

# combatstick button for zoom axis toggle
# pedals right for zoom past ZOOM_MAX
FREETRACK_KEY = "CONTROL SHIFT ALT F"
ZOOM_MIN = 1.0
ZOOM_MAX = 0.35
ZOOM_AXIS = 2
zoomedOut = state.get("zoomedout")
zoomButton = combatstick.getButton(3)
if state.toggle("zoom-toggle", zoomButton) or zoomedOut == None:
    log.info("zoom in" if zoomedOut else "zoom out")
    zoomedOut = not zoomedOut
    state.set("zoomedout", zoomedOut)
    
zoom = ZOOM_MIN if zoomedOut else ZOOM_MAX - (pedals.getAxis(1,0.25)+1)/2

zoomHistory = state.get("zoom-history", [])
zoomHistory.append(zoom)
if len(zoomHistory)>10:
    zoomHistory.pop(0)
vjoy.setAxis(ZOOM_AXIS, sum(zoomHistory)/len(zoomHistory))

# combatstick zoom axis button long press for Freetrack reset
if state.toggle("freetrack-reset", zoomButton, 1):
    log.info("reset freetrack")
    keyboard.click(FREETRACK_KEY)

# combatstick button for Teamspeak PTT
TEAMSPEAK_KEY = 'CONTROL SHIFT ALT T'
ptt = combatstick.getButton(2)
optt = state.set("ptt", ptt)
if ptt != optt:
    log.info("PTT %d" % ptt)
    if ptt: keyboard.press(TEAMSPEAK_KEY)
    else: keyboard.release(TEAMSPEAK_KEY)

# encoder 1 for two axis (one rotation) w/push selector
RADAR_ELEVATION_AXIS = 3
RANGE_AXIS = 4
 
encoder = phidgets.get(82141)

if not encoder.getInputState(0):
    vjoy.setAxis(RADAR_ELEVATION_AXIS, phidgets.getAxis(encoder, "radar-elevation", 3, 0.0))
else:
    vjoy.setAxis(RANGE_AXIS, phidgets.getAxis(encoder, "range", 1, 0.0))
    
# encoder 2 for axis (one rotation) and button 
MSL_VOLUME_AXIS = 5
MSL_UNCAGE_BUTTON = 1

encoder = phidgets.get(82081)

vjoy.setAxis(MSL_VOLUME_AXIS, phidgets.getAxis(encoder, "msl-volume", 1, 1.0))
vjoy.setButton(MSL_UNCAGE_BUTTON, encoder.getInputState(0))


# encoder 1 for hsi hdg/course inc/dec
# Note: the only way to click hdg/crs up or down is to send multiple subsequent keyboard presses
#       for each respective gauge modifier (-/+)1, (-/+)5 respectively. By sending only one 
#       keystroke per sync the call doesn't take too long and it stays responsive while remembering
#       remaining delta.  
#tuner = phidgets.get(82141)
#dial = 'hdg' if not tuner.getInputState(0) else 'crs'
#delta = phidgets.delta(tuner, 45) + state.get(dial, 0)
#if delta!=0:
#    if delta>=5: inc = 5
#    elif delta>=1: inc = 1
#    elif delta>-5: inc = -1
#    else: inc = -5
#    delta -= inc
#    keys = { "hdg-1":"CTRL ALT V", "hdg+1":"CTRL ALT B", "hdg-5":"SHIFT ALT V", "hdg+5":"SHIFT ALT B" ,
#             "crs-1":"CTRL ALT N", "crs+1":"CTRL ALT M", "crs-5":"SHIFT ALT N", "crs+5":"SHIFT ALT M" }
#    keyboard.click( keys[ "%s%+d" % (dial,inc) ]  )
#state.set(dial, delta) # remaining
    
# saitek axis 2 into 2 buttons (AFBrakesOut/AFBrakesIn)
AIRBREAK_OUT_BUTTON = 2
AIRBREAK_IN_BUTTON = 3

saitek = joysticks.get('Saitek Pro Flight Quadrant')
speedbrake = saitek.getAxis(1)
retract = speedbrake < -0.5
extend = speedbrake > 0.5
if state.set("sbe", extend) != extend and extend:
    log.info("extending speed brakes")
if state.set("sbr", retract) != retract and retract:
    log.info("retracting speed brakes")
vjoy.setButton(AIRBREAK_OUT_BUTTON, extend)
vjoy.setButton(AIRBREAK_IN_BUTTON, retract)


# saitek axis 3 into 2 buttons (AFGearUp, AFGearDown)
GEAR_UP_BUTTON = 4
GEAR_DOWN_BUTTON = 5

handleDown = saitek.getAxis(2) > 0.25
if handleDown: # let's not accidentially retract gear unless we've seen handle down first
    state.set("gear-seen-down", True)
handleUp = saitek.getAxis(2) < -0.25 and state.get("gear-seen-down")
gear = (handleUp,handleDown)
if state.set("gear", gear) != gear:
    log.info("Gear handle up=%s, down=%s" % (handleUp, handleDown))
vjoy.setButton(GEAR_UP_BUTTON, handleUp)
vjoy.setButton(GEAR_DOWN_BUTTON, handleDown)

# Missile/Dogfight override for
#    g_bHotasDgftSelfCancel 1  // SRM and MRM override callbacks call the override cancel callback when depressed
OVERRIDE_UP = 0
OVERRIDE_DOWN = 1

OVERRIDE_MRM = 6
OVERRIDE_DOG = 7

OVERRIDE_HOLD_SECONDS = 0.25

override = state.get("override", 0)
if override>=0 and state.toggle("override-up", throttle.getButton(OVERRIDE_UP), OVERRIDE_HOLD_SECONDS):
    override -= 1
if override<=0 and state.toggle("override-down", throttle.getButton(OVERRIDE_DOWN), OVERRIDE_HOLD_SECONDS):
    override += 1
if override != state.set("override", override):
    log.info("Override %d" % override)
vjoy.setButton(OVERRIDE_MRM, override<0)
vjoy.setButton(OVERRIDE_DOG, override>0)
