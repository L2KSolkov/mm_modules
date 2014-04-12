 # ------------------------------------------------------------------------
 # Module: IdleKick.py
 # Authors: xlr8or, www.xlr8or.com
 # Version 2.02
 # Description:
 #   This script kicks players who are idle, based on the configuration settings below.
 # Requirements:
 #   None.
 # Installation:
 #   Save this script as 'IdleKick.py' in your <bf2>/admin/standard_admin directory,
 #   and add the lines 'import IdleKick' and 'IdleKick.init()' to the file
 #   '<bf2>/admin/standard_admin/__init__.py'.
 # Credit:
 #   This script is based on the pingkick script from the guys at bf2.no
 #   Format is mainly the same as what they did, and where I could use their
 #   code I have shamelessly done so. 
 #   Credit therefor goes to Kybber and Panic, Battlefield.no
 # History:
 #   Autobalancing is a nice feature, but not when a large part of your team
 #   is doing something else, while staying ingame to not lose their slot.
 #   BF2 does not have a spectator ability, so if you're not participating,
 #   you're letting your team down!
 # Version 1.00 to 2.00:
 #   Cleaned some code up, added the ability to exclude clanmembers.
 # Version 2.00 to 2.01:
 #   Cleaned and corrected some global def's.
 # Version 2.01 to 2.02:
 #   Fixed the clantag protection.
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 #                     C O N F I G U R A T I O N
 # ------------------------------------------------------------------------
 # Settings for auto-kicking:
 autokick    = 1      # Enables/disables autokicking
 warnings    = 10     # The number of checks/warns a player has to fail/get before being kicked
 interval    = 30     # The interval between idle checks
 minplayers  = 5      # The minimum ammount of players online before checking idle players.
 announceme  = 0      # Announce the module at roundstart?
 warnme      = 1      # Warn the idle player 3 intervals before the maximum nr of warnings is reached?
 
 clantags = ["[XLR]","[xlr]","xlr8or"] # Clantags to protect from being kicked
 
 # ------------------------------------------------------------------------
 #                        I M P O R T
 # ------------------------------------------------------------------------
 
 import host
 import bf2
 from bf2 import g_debug
 
 # ------------------------------------------------------------------------
 #                       V A R I A B L E S
 # ------------------------------------------------------------------------
 
 # Let's set up our debug flag:
 xlr_debug = False
 
 # The timers:
 IkCheckTimer    = None  # Timer firing off the idle checker. Depends on the 'interval' variable.
 KickTimer       = None  # Timer that delays kicking after the final warning has been issued.
 AnnounceTimer   = None  # Timer that delays the "activated" message after entering bf2.GameStatus.Playing
 
 # List of people to kick for high idle. Will contain touples of p.index and p.getProfileId():
 kicklist = []
 
 # For keeping track of the game status:
 gamestatus = None
 
 
 # ------------------------------------------------------------------------
 #                       F U N C T I O N S
 # ------------------------------------------------------------------------
 
 # ------------------------------------------------------------------------
 # The init function is run by the standard_admin/__init__ functions:
 # ------------------------------------------------------------------------
 def init():
 
    if g_debug or xlr_debug: print 'IDLEKICK: initializing IdleKick script'
    # Force at least 20 seconds between idle checks:
    if interval < 10: interval = 10
    # Print debug message if autokick is disabled:
    if autokick != 1:
       if g_debug or xlr_debug: print 'IDLEKICK: Idle autokick not enabled'
    
    # Autokick is enabled, so hook it up:
    else:
       if g_debug or xlr_debug: print 'IDLEKICK: Enabling kick for being idle. Max. checkfails = %s.' % (warnings)
 
       # Register 'PlayerConnect' callback:
       host.registerHandler('PlayerConnect', onPlayerConnect, 1)
       host.registerHandler('PlayerSpawn', onPlayerSpawn, 1)
       host.registerGameStatusHandler(onGameStatusChanged)
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Callback function for the "PlayerConnect" event:
 # ------------------------------------------------------------------------
 def onPlayerConnect(p):
    #Resets the idle warning counter for the player
    resetPlayer(p)
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Callback function for the "PlayerSpawn" event:
 # ------------------------------------------------------------------------
 def onPlayerSpawn(p,s):
    # Sets the 'actuallyPlaying' flag for the player
    p.actuallyPlaying = True
    # We can reset the warnings, since the player has actually spawned.
    p.idleWarnings = 0
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Callback function for the "PreGame" game status event:
 # ------------------------------------------------------------------------
 def onGameStatusChanged(status):
    # Enables the idle check timer
    # Import variables, and update the game status:
    global gamestatus, kicklist, AnnounceTimer
    
    gamestatus = status
    if gamestatus == bf2.GameStatus.Playing:
       if announceme ==1:
          if g_debug or xlr_debug: print "IDLEKICK: Round Started. Setting AnnounceTimer"
          AnnounceTimer = bf2.Timer(onAnnounceTimer,10,1)
       if g_debug or xlr_debug: print "IDLEKICK: Round Started. (Re-)enabling check-timer"
       # Enable the idle check timer:
       enableCheckTimer()
    elif gamestatus == bf2.GameStatus.PreGame:
       if g_debug or xlr_debug: print "IDLEKICK: Game status changed to PreGame. Killing check-timer"
       # Kill the check-timer
       disableCheckTimer()
    elif gamestatus == bf2.GameStatus.Paused:
       if g_debug or xlr_debug: print "IDLEKICK: Game status changed to Paused. Killing check-timer"
       # Kill the check-timer
       disableCheckTimer()
    elif gamestatus == bf2.GameStatus.EndGame:
       if g_debug or xlr_debug: print "IDLEKICK: Game status changed to EndGame. Reset Players, Kicklist and killing check-timer"
       # Kill the check-timer
       disableCheckTimer()
       # Reset the kicklist
       kicklist = []
       # Reset players:
       resetPlayers()
 # ------------------------------------------------------------------------
 
 
 
 # ------------------------------------------------------------------------
 # Reset the idlescript variables placed in the player object:
 # ------------------------------------------------------------------------
 def resetPlayers():
    # Reset Warnings and stuff:
    if g_debug or xlr_debug: print "IDLEKICK: Resetting Players"
    for p in bf2.playerManager.getPlayers():
       resetPlayer(p)
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Reset the idlescript variables placed in the player object:
 # ------------------------------------------------------------------------
 def resetPlayer(p):
    # Reset Warnings and stuff:
    p.idleWarnings = 0
    p.actuallyPlaying = False
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Callback function for timer, that delays a message at round start:
 # ------------------------------------------------------------------------
 def onAnnounceTimer(data):
    global AnnounceTimer
    
    if g_debug or xlr_debug: print "IDLEKICK: Entering onAnnounceTimer... Sending the Activated announcement"
    msg = "Activated! Kicking after " + str(warnings) + " checks."
    sendMsg(msg)
    AnnounceTimer.destroy()
    AnnounceTimer = None
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Send text messages to the server, using rcon game.sayAll:
 # ------------------------------------------------------------------------
 def sendMsg(msg):
    # Sure you can edit this. But hey, why not give us the credit? ;-)
    host.rcon_invoke("game.sayAll \"[XLR]No-Idle: " + str(msg) + "\"")
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Enable the KickTimer:
 # ------------------------------------------------------------------------
 def enableKickTimer():
    # Enables the timer that runs the 'kickPlayers' functions
    global KickTimer
    
    if g_debug or xlr_debug: print "IDLEKICK: Enabling the kicktimer..."
    KickTimer = bf2.Timer(kickPlayers, 5, 1)
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Enable the IkCheckTimer:
 # ------------------------------------------------------------------------
 def enableCheckTimer():
    # Enables the timer that runs the 'checkidle' function
    global IkCheckTimer
    
    if IkCheckTimer:
       if g_debug or xlr_debug: print "IDLEKICK: IkCheckTimer (already) running: Next check @ %s" % (IkCheckTimer.getTime())
       return True
    else:
       # Create the timer:
       if g_debug or xlr_debug: print "IDLEKICK: Timer not enabled. Enabling..."
       IkCheckTimer = bf2.Timer(checkidle, interval, 1)
       IkCheckTimer.setRecurring(interval)
       # Print debug message telling the status of the timer:
       if IkCheckTimer:
          if g_debug or xlr_debug: print "IDLEKICK: First check @ %s" % (IkCheckTimer.getTime())
          return True
       else:
          if g_debug or xlr_debug: print "IDLEKICK: ERROR: IkCheckimer Not enabled in def enableCheckTimer()"
          return False
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Disable the IkCheckTimer:
 # ------------------------------------------------------------------------
 def disableCheckTimer():
    global IkCheckTimer
    
    IkCheckTimer.destroy()
    IkCheckTimer = None
 
 # ------------------------------------------------------------------------
 
 # ------------------------------------------------------------------------
 # Loop all players, checking their idle, kick high-idleer:
 # ------------------------------------------------------------------------
 def checkidle(data):
    # Checks idle of all players, and kicks idlers
    global kicklist, gamestatus
 
    # We only want to check idle during rounds:
    if gamestatus != bf2.GameStatus.Playing: return
    
    # Make sure our timer is enabled:
    if not enableCheckTimer(): return
    
    if bf2.playerManager.getNumberOfPlayers() < minplayers:
       if g_debug or xlr_debug: print "IDLEKICK: Not enough players to check for idlers..."
       return
 
    if g_debug or xlr_debug: print "IDLEKICK: Running checkidle"
 
    # Loop all players
    for p in bf2.playerManager.getPlayers():
       # Do not check players that haven't completed their "connect" yet:
       if not p.isConnected(): 
         if g_debug or xlr_debug: print "IDLEKICK: Player not yet connected, continuing..."
         continue
       if p.isAlive(): 
         if g_debug or xlr_debug: print "IDLEKICK: Player is already playing, continuing..."
         continue
       if p.isManDown(): 
         if g_debug or xlr_debug: print "IDLEKICK: Player in ManDown state, continuing..."
         continue
       # Get the player name. We'll use it often:
       name = str(p.getName())
 
       # Prevent Clanmembers from being kicked
       skip = 0
       for clantag in clantags:
         if name.find(clantag)>-1: 
           skip = 1
           break
       if skip == 1: continue
 
       # If we have a valid idle, check it, and issue a warning if the idle exceeds the limit:
       p.idleWarnings += 1
       if g_debug or xlr_debug: print "IDLEKICK: Player " + name + " has been detected as idle " + str(p.idleWarnings) + " time(s)"
       if warnme == 1 and p.idleWarnings == (warnings - 3): 
         #tmp = p.idleWarnings * interval / 60
         sendMsg("WARNING: " + name + " has not returned to duty for quite some time now. Move in fast, you're about to be court marshalled!")
       # Issue a warning if a player has reached the maximum number of warnings. Will be kicked next time 'checkidle' is run:
       if warnings <= p.idleWarnings:
         #tmp = p.idleWarnings * intervals / 60
         sendMsg("Desertion Violation: " + name + " is being removed for not returning to duty in time! (aka idling)")
         # Add the player to the kicklist:
         kicklist.append((p.index,p.getProfileId()))
 
    # Check of we shall enable the kicktimer:
    if len(kicklist):
       enableKickTimer()
 # ------------------------------------------------------------------------
 
 
 # ------------------------------------------------------------------------
 # Function run by the kicktimer:
 # ------------------------------------------------------------------------
 def kickPlayers(data):
    # Loops through 'kicklist', and kicks players accordingly.
    #print "IDLEKICK: kickPlayers..."
    global kicklist, KickTimer
    
    for i in kicklist:
       p = bf2.playerManager.getPlayerByIndex(i[0])
       # Make sure we're not kicking a player that has gotten an already disconnected "violater's" index:
       if not p.getProfileId() == i[1]: continue
       # Check if this player indeed has reached the limit for maximum warnings
       if warnings <= p.idleWarnings:
          # Kick if limit is reached:
          if g_debug or xlr_debug: print "IDLEKICK: Kicking player " + p.getName() + " for being idle."
          result = host.rcon_invoke("admin.kickPlayer " + str(p.index)) 
    kicklist = []
    KickTimer.destroy()
    KickTimer = None
 # ------------------------------------------------------------------------