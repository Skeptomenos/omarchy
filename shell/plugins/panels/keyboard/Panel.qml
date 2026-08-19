import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import qs.Ui

// Keyboard backlight settings overlay. The slider reads and writes percentages
// through omarchy-brightness-keyboard, so device discovery and validation stay
// in one place. Changes apply on release to avoid spawning a process for every
// pointer movement.
//
// Summon with: omarchy-shell shell summon omarchy.keyboard
Item {
  id: root

  property var shell: null
  property var manifest: null

  property bool opened: false
  property bool loading: true
  property bool loaded: false
  property bool applying: false
  property bool writeFailed: false
  property int currentPercent: 0
  property int pendingPercent: 0
  property string readContext: "initial"
  property string errorMessage: ""
  readonly property bool controlsEnabled: root.opened && root.loaded
    && !root.loading && !root.applying && !readProc.running && !writeProc.running

  function open(payloadJson) {
    opened = true
    if (!readProc.running && !writeProc.running) {
      errorMessage = ""
      applying = false
      startRead("initial")
    }
    Qt.callLater(function() {
      if (root.opened) keyCatcher.forceActiveFocus()
    })
  }

  function close() {
    opened = false
  }

  function dismiss() {
    if (root.shell && typeof root.shell.hide === "function")
      root.shell.hide((root.manifest && root.manifest.id) || "omarchy.keyboard")
    else close()
  }

  function startRead(context) {
    if (readProc.running) return false
    readContext = context
    loading = true
    loaded = false
    readProc.running = true
    return true
  }

  function applyPercent(value) {
    if (!controlsEnabled) return false
    var percent = Math.max(0, Math.min(100, Math.round(value)))
    pendingPercent = percent
    applying = true
    writeFailed = false
    errorMessage = ""
    writeProc.running = true
    return true
  }

  function stepPercent(delta) {
    return applyPercent(currentPercent + delta)
  }

  Process {
    id: readProc
    command: ["omarchy-brightness-keyboard", "--no-osd", "get"]

    stdout: StdioCollector {
      id: readOutput
      waitForEnd: true
    }

    onExited: function(exitCode) {
      var raw = String(readOutput.text || "").trim()
      var valid = exitCode === 0 && /^\d{1,3}$/.test(raw)
      var percent = valid ? parseInt(raw, 10) : -1
      valid = valid && percent >= 0 && percent <= 100

      root.loading = false
      root.loaded = valid
      if (valid) root.currentPercent = percent

      if (root.readContext === "confirm") {
        root.applying = false
        if (root.writeFailed)
          root.errorMessage = "Could not set brightness"
        else if (!valid)
          root.errorMessage = "Could not confirm brightness"
        else
          root.errorMessage = ""
      } else {
        root.errorMessage = valid ? "" : "Could not read brightness"
      }
    }
  }

  Process {
    id: writeProc
    command: [
      "omarchy-brightness-keyboard", "--no-osd", "set",
      String(root.pendingPercent)
    ]

    onExited: function(exitCode) {
      root.writeFailed = exitCode !== 0
      root.startRead("confirm")
    }
  }

  PanelWindow {
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "omarchy-keyboard"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

    Rectangle {
      anchors.fill: parent
      color: Qt.rgba(0, 0, 0, 0.45)

      MouseArea {
        anchors.fill: parent
        onClicked: root.dismiss()
      }
    }

    Item {
      id: keyCatcher
      anchors.fill: parent
      focus: true

      Keys.onEscapePressed: root.dismiss()
      Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Left || event.key === Qt.Key_Down
            || event.key === Qt.Key_H) {
          root.stepPercent(-5)
          event.accepted = true
        } else if (event.key === Qt.Key_Right || event.key === Qt.Key_Up
                   || event.key === Qt.Key_L) {
          root.stepPercent(5)
          event.accepted = true
        } else if (event.key === Qt.Key_Home) {
          root.applyPercent(0)
          event.accepted = true
        } else if (event.key === Qt.Key_End) {
          root.applyPercent(100)
          event.accepted = true
        }
      }

      Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(Style.space(420), keyCatcher.width - Style.space(32))
        height: content.implicitHeight + Style.space(48)
        radius: Style.cornerRadius
        color: Color.background
        border.width: Math.max(1, Style.space(2))
        border.color: Color.popups.border

        // Swallow clicks so only the scrim outside the card dismisses.
        MouseArea { anchors.fill: parent; onClicked: {} }

        ColumnLayout {
          id: content
          anchors.fill: parent
          anchors.margins: Style.space(24)
          spacing: Style.space(16)

          Text {
            text: "KEYBOARD BACKLIGHT"
            color: Color.foreground
            font.family: Style.font.family
            font.pixelSize: Style.font.caption
            font.bold: true
            font.letterSpacing: 2
          }

          RowLayout {
            Layout.fillWidth: true

            Text {
              text: "Brightness"
              color: Color.foreground
              font.family: Style.font.family
              font.pixelSize: Style.font.bodySmall
              Layout.fillWidth: true
            }

            Text {
              text: root.applying ? "Applying…"
                : root.loading ? "Loading…"
                : root.loaded ? root.currentPercent + "%" : "Unavailable"
              color: root.loaded && !root.loading ? Color.accent : Qt.darker(Color.foreground, 1.6)
              font.family: Style.font.family
              font.pixelSize: Style.font.bodySmall
              font.bold: true
            }
          }

          PanelSlider {
            Layout.fillWidth: true
            enabled: root.controlsEnabled
            opacity: root.controlsEnabled ? 1.0 : 0.45
            minimum: 0
            maximum: 100
            step: 1
            integer: true
            value: root.currentPercent
            onMoved: function(value) {
              root.currentPercent = Math.round(value)
            }
            onReleased: function(value) {
              root.applyPercent(value)
            }
          }

          Text {
            visible: root.errorMessage !== ""
            text: root.errorMessage
            color: Color.urgent
            font.family: Style.font.family
            font.pixelSize: Style.font.caption
            Layout.alignment: Qt.AlignHCenter
          }

          Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Color.popups.border
          }

          RowLayout {
            Layout.fillWidth: true
            spacing: Style.space(12)

            Text {
              text: "Shift+F1"
              color: Color.accent
              font.family: Style.font.family
              font.pixelSize: Style.font.bodySmall
              font.bold: true
              Layout.preferredWidth: Style.space(96)
            }

            Text {
              text: "Backlight down"
              color: Color.foreground
              font.family: Style.font.family
              font.pixelSize: Style.font.bodySmall
              Layout.fillWidth: true
            }
          }

          RowLayout {
            Layout.fillWidth: true
            spacing: Style.space(12)

            Text {
              text: "Shift+F2"
              color: Color.accent
              font.family: Style.font.family
              font.pixelSize: Style.font.bodySmall
              font.bold: true
              Layout.preferredWidth: Style.space(96)
            }

            Text {
              text: "Backlight up"
              color: Color.foreground
              font.family: Style.font.family
              font.pixelSize: Style.font.bodySmall
              Layout.fillWidth: true
            }
          }

          Text {
            text: "Esc or click outside to close"
            color: Qt.darker(Color.foreground, 1.6)
            font.family: Style.font.family
            font.pixelSize: Style.font.caption
            Layout.alignment: Qt.AlignHCenter
          }
        }
      }
    }
  }
}
