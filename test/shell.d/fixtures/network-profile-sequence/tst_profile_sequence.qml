import QtQuick
import QtTest
import "../../../../shell/plugins/panels/network/Model.js" as Model

TestCase {
  name: "NetworkProfileSequence"
  when: windowShown
  width: 400
  height: 300

  property var rows: []

  ListView {
    id: networkList
    width: 400
    height: 300
    model: rows
    delegate: Item {
      required property var modelData
      width: 400
      height: 50
    }
  }

  function cleanup() {
    rows = []
    networkList.forceLayout()
    tryCompare(networkList, "count", 0)
  }

  function test_profileSelection_data() {
    return [
      {
        tag: "single-active",
        uuids: ["uuid-home"],
        raw: "uuid-home:802-11-wireless:yes:100:yes\n",
        expected: "uuid-home"
      },
      {
        tag: "active-before-newer",
        uuids: ["uuid-newer", "uuid-home"],
        raw: "uuid-newer:802-11-wireless:no:200:no\nuuid-home:802-11-wireless:yes:100:yes\n",
        expected: "uuid-home"
      },
      {
        tag: "newest-inactive",
        uuids: ["uuid-old", "uuid-newer"],
        raw: "uuid-old:802-11-wireless:yes:100:no\nuuid-newer:802-11-wireless:no:200:no\n",
        expected: "uuid-newer"
      },
      {
        tag: "tied-inactive",
        uuids: ["uuid-a", "uuid-b"],
        raw: "uuid-a:802-11-wireless:yes:100:no\nuuid-b:802-11-wireless:no:100:no\n",
        expected: ""
      },
      {
        tag: "multiple-active",
        uuids: ["uuid-a", "uuid-b", "uuid-newer"],
        raw: "uuid-a:802-11-wireless:yes:100:yes\nuuid-b:802-11-wireless:no:200:yes\nuuid-newer:802-11-wireless:yes:300:no\n",
        expected: ""
      },
      {
        tag: "unknown-profile",
        uuids: ["uuid-missing"],
        raw: "uuid-home:802-11-wireless:yes:100:yes\n",
        expected: ""
      },
      {
        tag: "duplicate-profile",
        uuids: ["uuid-home", "uuid-home"],
        raw: "uuid-home:802-11-wireless:yes:100:yes\n",
        expected: "uuid-home"
      },
      {
        tag: "non-string-entries",
        uuids: [null, 42, { uuid: "uuid-home" }, "uuid-home"],
        raw: "uuid-home:802-11-wireless:yes:100:yes\n",
        expected: "uuid-home"
      }
    ]
  }

  function test_profileSelection(data) {
    var row = Model.wifiRow({
      connected: true,
      known: true,
      name: "Fixture",
      signalStrength: 0.8,
      security: 1,
      nmSettings: []
    })
    row.profileUuids = data.uuids
    var profiles = Model.parseAutoConnectProfiles(data.raw)
    var keyboardProfile = Model.selectAutoConnectProfile(row.profileUuids, profiles)
    compare(keyboardProfile ? keyboardProfile.uuid : "", data.expected, "keyboard row selection")

    rows = [row]
    networkList.forceLayout()
    tryVerify(function() { return networkList.currentItem !== null })
    var delegateRow = networkList.currentItem.modelData
    var visibleProfile = Model.selectAutoConnectProfile(delegateRow.profileUuids, profiles)
    compare(visibleProfile ? visibleProfile.uuid : "", data.expected, "native delegate selection")
  }
}
