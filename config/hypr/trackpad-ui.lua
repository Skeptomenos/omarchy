-- Managed by omarchy-trackpad-settings (Omarchy menu: Setup > Trackpad).
-- Manual edits will be overwritten; loaded after hypr/input.lua so these win.
-- state: gestures=on swipe=1.00
hl.config({
  input = {
    sensitivity = 0.00,
    touchpad = {
      natural_scroll = true,
      scroll_factor = 1.00,
    },
  },
})

-- Mac-style four-finger gestures. scale sets how far fingers travel per
-- workspace: higher is faster.
hl.gesture({ fingers = 4, direction = "horizontal", action = "workspace", scale = 1.00 })
hl.gesture({ fingers = 4, direction = "up", action = "fullscreen" })
hl.gesture({ fingers = 4, direction = "down", action = "special", workspace_name = "scratchpad" })
