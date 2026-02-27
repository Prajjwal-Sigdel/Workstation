/**
 * Sleep Checker - KWin Idle Dim Detection Script
 * 
 * Emits a custom D-Bus signal when the screen dims/blanks due to inactivity.
 * The Python service subscribes to this signal to trigger face detection.
 * 
 * Signal: org.sleepchecker.IdleNotifier.screenDimmed(boolean)
 *   - true  → Screen dimming/blanking from inactivity → Start face detection
 *   - false → User activity detected → Stop detection / release inhibitors
 * 
 * Only fires on inactivity-based events, NOT on lid close or sleep button.
 */
(function () {
    "use strict";

    var SERVICE   = "org.sleepchecker.IdleNotifier";
    var PATH      = "/org/sleepchecker/IdleNotifier";
    var INTERFACE = "org.sleepchecker.IdleNotifier";
    var SIGNAL    = "screenDimmed";

    var currentlyDimmed = false;

    function emitSignal(isDimmed) {
        callDBus(SERVICE, PATH, INTERFACE, SIGNAL, isDimmed);
    }

    function onIdleDetected(source) {
        if (!currentlyDimmed) {
            currentlyDimmed = true;
            emitSignal(true);
            print("SleepChecker: Idle detected (" + source + ") → signal emitted");
        }
    }

    function onActivityDetected(source) {
        if (currentlyDimmed) {
            currentlyDimmed = false;
            emitSignal(false);
            print("SleepChecker: Activity detected (" + source + ") → signal emitted");
        }
    }

    // ─────────────────────────────────────────────
    //  IDLE TRIGGERS (earliest to latest)
    // ─────────────────────────────────────────────

    // 1. Display about to turn off (DPMS) - EARLIEST signal
    //    Fires before screen locks, when display is about to blank
    if (typeof workspace.screens !== "undefined") {
        workspace.screens.forEach(function (output) {
            if (output.aboutToTurnOff) {
                output.aboutToTurnOff.connect(function () {
                    onIdleDetected("display turning off");
                });
            }
        });
    }

    // 2. Screen about to lock - FALLBACK if aboutToTurnOff unavailable
    //    Fires when lock screen is about to appear
    if (workspace.hasOwnProperty("screenAboutToLock")) {
        workspace.screenAboutToLock.connect(function () {
            onIdleDetected("screen about to lock");
        });
    }

    // ─────────────────────────────────────────────
    //  ACTIVITY TRIGGERS (user is back)
    // ─────────────────────────────────────────────

    // Display woke up from DPMS
    if (typeof workspace.screens !== "undefined") {
        workspace.screens.forEach(function (output) {
            if (output.wakeUp) {
                output.wakeUp.connect(function () {
                    onActivityDetected("display woke up");
                });
            }
        });
    }

    if (workspace.hasOwnProperty("screenUnlocked")) {
        workspace.screenUnlocked.connect(function () {
            onActivityDetected("screen unlocked");
        });
    }

    if (workspace.hasOwnProperty("currentDesktopChanged")) {
        workspace.currentDesktopChanged.connect(function () {
            onActivityDetected("desktop switched");
        });
    }

    if (workspace.hasOwnProperty("windowActivated")) {
        workspace.windowActivated.connect(function () {
            onActivityDetected("window focus changed");
        });
    }

    if (workspace.hasOwnProperty("cursorPosChanged")) {
        workspace.cursorPosChanged.connect(function () {
            onActivityDetected("cursor moved");
        });
    }

    print("SleepChecker: KWin idle detection script loaded");
    print("SleepChecker: Signal → " + INTERFACE + "." + SIGNAL);
    print("SleepChecker: Monitoring " + (typeof workspace.screens !== "undefined" ? workspace.screens.length : 0) + " screen(s)");
})();
