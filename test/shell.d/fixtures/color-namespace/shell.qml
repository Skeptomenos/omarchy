import QtQuick
import Quickshell
import qs.Commons
import qs.Commons as Commons
import qs.Commons as Shared
import qs.Ui as Ui

// No windows, IPC handlers or desktop services. Exercise the real QML modules.
ShellRoot {
  id: root

  property int accentChanges: 0
  property int attempts: 0
  property var failures: []
  readonly property color stateColor: Style.resolveStateColor("accent")
  readonly property var menuBorder: Border.surfaceSpec("menu", "border", "#000000", 1)

  Connections {
    target: Commons.Color
    function onAccentChanged() { root.accentChanges++ }
  }

  Ui.WidgetButton { id: widget; text: "test" }
  Ui.OpticalGlyph { id: glyph; text: "A" }

  function check(condition, message) {
    if (!condition) failures.push(message)
  }

  function color(actual, expected, message) {
    check(actual !== undefined && Qt.colorEqual(actual, expected),
      message + ": expected " + expected + ", got " + actual)
  }

  function paletteAccent(palette) {
    return palette.accent
  }

  function initial() {
    try {
      check(Commons.Color === Shared.Color, "namespace imports share one palette singleton")
      check(Style === Commons.Style && Border === Commons.Border, "existing imports retain singleton identity")
      color(Commons.Color.foreground, "#d7e8f9", "startup palette foreground")
      color(Commons.Color.menu.text, "#c0ffee", "startup menu text")
      color(Commons.Color.menu.background, "#203040", "startup menu background")
      color(paletteAccent(Commons.Color), "#2468ac", "palette object function argument")
      color(widget.foreground, "#d7e8f9", "WidgetButton default foreground")
      color(widget.activeColor, "#a12b3c", "WidgetButton default urgent")
      color(glyph.color, "#d7e8f9", "OpticalGlyph shares the palette")
      color(stateColor, "#2468ac", "Style internal fallback lookup")
      color(Style.normalFill, "#2468ac", "Style internal convenience binding")
      color(menuBorder.color, "#2468ac", "Border internal palette role lookup")
      check(menuBorder.widths.top === 3, "Border reads the shared shell values")

      accentChanges = 0
      Shared.Color.loadColors('foreground = "#f1e2d3"\nbackground = "#302010"\naccent = "#9753bd"\nred = "#7b1839"')
      Shared.Color.loadShell('[menu]\ntext = "#abcdef"\nbackground = "#213141"\nborder = "urgent"\nborder-width = 5\n[controls]\nnormal-color = "background"\nnormal-fill-alpha = 1')
      Qt.callLater(updated)
    } catch (error) {
      failures.push("initial exception: " + error)
      finish()
    }
  }

  function updated() {
    try {
      color(Commons.Color.accent, "#9753bd", "shared singleton mutation")
      color(Commons.Color.menu.text, "#abcdef", "menu text update")
      color(Commons.Color.menu.background, "#213141", "menu background update")
      color(widget.foreground, "#f1e2d3", "WidgetButton foreground update")
      color(widget.activeColor, "#7b1839", "WidgetButton urgent update")
      color(glyph.color, "#f1e2d3", "OpticalGlyph foreground update")
      color(stateColor, "#9753bd", "Style fallback binding update")
      color(Style.normalFill, "#302010", "Style shell and palette update")
      color(menuBorder.color, "#7b1839", "Border role update")
      check(menuBorder.widths.top === 5, "Border shell width update")
      check(accentChanges === 1, "Connections receives exactly one accent change, got " + accentChanges)
    } catch (error) {
      failures.push("update exception: " + error)
    }
    finish()
  }

  function finish() {
    if (failures.length) {
      console.log("RESULT fail color namespace\n" + failures.join("\n"))
    } else {
      console.log("RESULT pass color namespace")
    }
    Qt.quit()
  }

  Timer {
    interval: 10
    running: true
    repeat: true
    onTriggered: {
      if (Commons.Color.colorsFile.loaded && Commons.Color.shellFile.loaded && Commons.Color.userShellFile.loaded) {
        stop()
        Qt.callLater(root.initial)
      } else if (++root.attempts === 200) {
        stop()
        root.failures.push("isolated theme files did not load")
        root.finish()
      }
    }
  }
}
