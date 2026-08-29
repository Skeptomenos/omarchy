"""Zero-child RED for the fixed isolated real-E execution boundary.

The test harness has one extra /inputs/test binding. The eventual production
launch has exactly eight task bindings. This runner authenticates those eight
inputs, proves the current pure 424-command plan, and then asks for three
missing execution primitives. It never calls a child runner or operational API.
"""

import ast
from collections.abc import Callable
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
import unittest


ORIGINAL_SYS_PATH = tuple(sys.path)
TEST = Path("/inputs/test")
PROOF = Path("/inputs/proof")
SUBJECT = Path("/inputs/recipe")
COMMANDS = Path("/inputs/subject/e_control.py")
CONTRACT = Path("/inputs/contract/image_contract.py")
ASSEMBLY = Path("/inputs/assembly/prepare_image.py")
CONTROL = Path("/inputs/control/verify_control.py")
HELPER = Path("/inputs/helper/cpio_image.py")
BASE = Path("/inputs/base")
INDEX_DIRECTORY = Path("/inputs/index-inputs")
SUBJECT_SHA256 = "57d35a30de9b351bcbaf0b78a1be186c8c44a2fbfb378d8f0b801e6e9256a7a9"
E_SHA256 = "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae"
E_BYTES = 19191513
SOURCE_INPUTS = (
  ("cpio_image", HELPER,
   "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58"),
  ("verify_control", CONTROL,
   "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8"),
  ("prepare_image", ASSEMBLY,
   "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60"),
  ("t1_image_contract", CONTRACT,
   "a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf"),
  ("e_control", COMMANDS,
   "16016875e731e88d047eb805c7c6d03045300abdb262361b18010a952adb7b80"),
)
PINS = {
  SUBJECT: SUBJECT_SHA256,
  **{path: digest for _, path, digest in SOURCE_INPUTS},
  BASE: E_SHA256,
  PROOF: "9133cb64040f9df0daf9aa0caaab913c90fe7ce5c9bf59a19c71ce3e36fb0c94",
}
INDEX_INPUTS = {
  "modules.order": (
    73113, "497c8546d3131d01191f7a66b68047abce5e5235ae982890180007f55c51a927",
  ),
  "modules.builtin": (
    10592, "74de5bab05fe70496f7702d83974adf8816ea826f1d8579f3b3f4b28a3890d2b",
  ),
  "modules.builtin.modinfo": (
    106640, "702d4cabaa9bdc1b282d0e419ba091f64dc06ba737fe7319928bb3003adeea4b",
  ),
}
SOURCE_LAYOUT = {
  HELPER.parent: HELPER.name,
  CONTROL.parent: CONTROL.name,
  ASSEMBLY.parent: ASSEMBLY.name,
  CONTRACT.parent: CONTRACT.name,
  COMMANDS.parent: COMMANDS.name,
}
PRODUCTION_BINDINGS = (
  "/inputs/recipe",
  "/inputs/subject",
  "/inputs/contract",
  "/inputs/assembly",
  "/inputs/control",
  "/inputs/helper",
  "/inputs/base",
  "/inputs/index-inputs",
)
TEST_TOP = frozenset((
  "proof", "test", "recipe", "subject", "contract", "assembly", "control",
  "helper", "base", "index-inputs",
))
SELECTED_TESTS = (
  "EExecutionRedTests.test_a_fixed_self_bootstrap_is_missing",
  "EExecutionRedTests.test_b_exact_execution_policy_is_missing",
  "EExecutionRedTests.test_c_bounded_operational_collector_is_missing",
)
PRODUCTION_COMMAND = (
  "/usr/bin/python3.14", "-I", "-S", "-B", "/inputs/recipe",
)
PRODUCTION_ENVIRONMENT = (
  ("PATH", "/usr/bin:/bin"),
  ("LC_ALL", "C"),
  ("TMPDIR", "/tmp"),
  ("PYTHONDONTWRITEBYTECODE", "1"),
)
RUNTIME_MOUNTS = 582
FIXED_SANDBOX_MOUNTS = 3
PRODUCTION_TASK_INPUTS = 8
PRODUCTION_READ_ONLY_MOUNTS = 593
TEST_TASK_INPUTS = 9
TEST_READ_ONLY_MOUNTS = 594
PLANNED_CHILDREN = 424
CONTROL_SECONDS = 270.0
CHILD_SECONDS = 30.0
WORKLOAD_SECONDS = 280
OUTER_SECONDS = 285
STDERR_LIMIT = 1
REPORT_LIMIT = 128 * 1024
EMPTY_CONFIG_LIMIT = 1
EARLY_STREAM_LIMIT = 10240
MAIN_STREAM_LIMIT = 61286668
RECORD_FILES = 1272
CONTROL_TREE_FILES = 214
LOOKUP_TREE_FILES = 207
TREE_DIRECTORIES = 48
TREE_MAX_DEPTH = 16
TREE_FILE_LIMIT = 2 * 1024 * 1024
TREE_AGGREGATE_LIMIT = 64 * 1024 * 1024
OPERATIONAL_RECORD_ROOT = "/work/e-control-children-e1"
OPERATIONAL_PATHS = (
  OPERATIONAL_RECORD_ROOT,
  "/work/control-root",
  "/work/lookup-root",
  "/work/empty-modprobe.conf",
  "/work/e-early.cpio",
  "/work/e-main.cpio",
)
PAYLOAD_LIMITS = (1213760, 12368, 66512, 20312)
STDOUT_LIMITS = (
  1024, 1024, 65536, 65536,
  E_BYTES - 10240,
  *PAYLOAD_LIMITS,
  1,
  128 * 1024, 128 * 1024,
  *((4096, 65536) * 200),
  *((65536,) * 12),
)
META = Path("/work/e-control-execution-red")
FORBIDDEN_OUTPUTS = (
  Path("/work/control-root"),
  Path("/work/lookup-root"),
  Path("/work/empty-modprobe.conf"),
  Path("/work/e-early.cpio"),
  Path("/work/e-main.cpio"),
  Path("/work/e-control-header.json"),
  Path("/work/e-control-evidence.json"),
  Path("/work/e-control-result.pending"),
  Path("/work/e-control-result.json"),
)
KERNEL = "7.1.6-1-1-ARCH"
PREFIX = f"usr/lib/modules/{KERNEL}/"
PAYLOADS = (
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x-core.ko",
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x.ko",
  PREFIX + "kernel/drivers/phy/apple/phy-apple-atc.ko",
  PREFIX + "kernel/drivers/usb/dwc3/dwc3-apple.ko",
)
ALIASES = (
  "of:Nusb-pdT(null)Capple,cd321x",
  "of:Ndwc3T(null)Capple,t8103-dwc3",
  "of:Natc-phyT(null)Capple,t8103-atcphy",
)
EXPORTS = (
  "tipd_sn201202x_data", "tps6598x_regmap_config", "tipd_init", "tipd_cd321x_data",
  "tipd_tps6598x_data", "tipd_tps25750_data", "tipd_remove", "tipd_suspend",
  "tipd_resume",
)


def require(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (
    info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
    info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns,
  )


def read_pinned(path: Path) -> tuple[bytes, tuple[int, ...]]:
  require(path in PINS, "unapproved input")
  for parent in path.parents:
    require(stat.S_ISDIR(parent.lstat().st_mode), "input parent is not a real directory")
  before = path.lstat()
  bound = E_BYTES if path == BASE else 128 * 1024
  expected_mode = 0o644 if path == SUBJECT else 0o600
  require(
    stat.S_ISREG(before.st_mode)
    and stat.S_IMODE(before.st_mode) == expected_mode
    and before.st_uid == before.st_gid == 1001
    and before.st_nlink == 1
    and 0 < before.st_size <= bound
    and (path != BASE or before.st_size == E_BYTES),
    "input metadata differs",
  )
  descriptor = os.open(
    path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
  )
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "input changed on open")
    raw = stream.read(bound + 1)
    require(
      identity(os.fstat(stream.fileno())) == identity(before) == identity(path.lstat()),
      "input changed while read",
    )
  require(len(raw) == before.st_size and sha256(raw) == PINS[path], "input hash mismatch")
  return raw, identity(before)


def read_index_directory() -> tuple[
  dict[str, bytes], tuple[int, ...], dict[str, tuple[int, ...]],
]:
  before = INDEX_DIRECTORY.lstat()
  require(
    stat.S_ISDIR(before.st_mode)
    and stat.S_IMODE(before.st_mode) == 0o700
    and before.st_uid == before.st_gid == 1001
    and before.st_nlink == 2,
    "index directory metadata differs",
  )
  require(
    {path.name for path in INDEX_DIRECTORY.iterdir()} == set(INDEX_INPUTS),
    "index directory membership differs",
  )
  raw_files: dict[str, bytes] = {}
  states: dict[str, tuple[int, ...]] = {}
  for name, (size, digest) in INDEX_INPUTS.items():
    path = INDEX_DIRECTORY / name
    before_file = path.lstat()
    require(
      stat.S_ISREG(before_file.st_mode)
      and stat.S_IMODE(before_file.st_mode) == 0o644
      and before_file.st_uid == before_file.st_gid == 1001
      and before_file.st_nlink == 1
      and before_file.st_size == size,
      "index input metadata differs",
    )
    descriptor = os.open(
      path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    with os.fdopen(descriptor, "rb") as stream:
      require(
        identity(os.fstat(stream.fileno())) == identity(before_file),
        "index input changed on open",
      )
      raw = stream.read(size + 1)
      require(
        identity(os.fstat(stream.fileno())) == identity(before_file)
        == identity(path.lstat()),
        "index input changed while read",
      )
    require(len(raw) == size and sha256(raw) == digest, "index input hash mismatch")
    raw_files[name] = raw
    states[name] = identity(before_file)
  require(identity(INDEX_DIRECTORY.lstat()) == identity(before), "index directory changed")
  return raw_files, identity(before), states


def validate_binding_tree() -> None:
  inputs = Path("/inputs")
  require(
    stat.S_ISDIR(inputs.lstat().st_mode)
    and {path.name for path in inputs.iterdir()} == TEST_TOP,
    "test input membership differs",
  )
  test_info = TEST.lstat()
  require(
    stat.S_ISREG(test_info.st_mode)
    and stat.S_IMODE(test_info.st_mode) == 0o644
    and test_info.st_uid == test_info.st_gid == 1001
    and test_info.st_nlink == 1
    and 0 < test_info.st_size < 128 * 1024,
    "runner metadata differs",
  )
  for directory, name in SOURCE_LAYOUT.items():
    info = directory.lstat()
    require(
      stat.S_ISDIR(info.st_mode)
      and stat.S_IMODE(info.st_mode) == 0o700
      and info.st_uid == info.st_gid == 1001
      and info.st_nlink == 2
      and {path.name for path in directory.iterdir()} == {name},
      "source binding membership or metadata differs",
    )


def load_source(name: str, path: Path, raw: bytes) -> ModuleType:
  require(name not in sys.modules, "source already imported")
  module = ModuleType(name)
  module.__file__ = str(path)
  sys.modules[name] = module
  exec(compile(raw, str(path), "exec"), module.__dict__)
  return module


BASELINE_TOP_LEVEL_MANIFEST = (
  ("expr:docstring", "94cd4e4bfcc948e5d3d61ec3b6440451334ba442b141c815bb23d20c1379c32c"),
  ("importfrom:dataclasses", "321ed2ed3afceb74be547c9905ed4c676e453b1a68fe7cb2d3e214caeac2624d"),
  ("import:ctypes", "669c8db7bfb9b4e64a7aa5f9239cbd229a5c460f228936e83d225f5ab2176b82"),
  ("import:errno", "90c7b14efdb367e3c6ed7be4c16022540b5f83b7feb5da8329e4718679b72e8b"),
  ("importfrom:fnmatch", "5a4d5aee3e8b8e43e04439231735e712438acb7be12f9452a6a6a3ad1da90da8"),
  ("import:hashlib", "092cb77ae0770f1627b29bf41b2732722fbcc3a0e1d77a79674801800a2721d1"),
  ("import:json", "211ee42757705c7e350e70e36b762987a737f5e9c268f2a343e2dbfcb8fbea75"),
  ("import:os", "ac3a74d6dd975a8e8fe4b7f85fce794793a9355595b850e3926964913948d386"),
  ("importfrom:pathlib", "59051b17634cdcb5a576ceb58fdc0a4e5652ed3b60d66667e92ddefd931abeca"),
  ("import:re", "6b81b4ca19c88ec507aad63f1f49291209368a9490113655a68e994c91d092c1"),
  ("import:stat", "c22b5a111acc3bea9e5136e41e207f1f95083e90d861516ce34d682526721c86"),
  ("importfrom:typing", "572213b85a348bcfded39f726167a1dff6bbee57af323ecff8413d18da40914d"),
  ("importfrom:cpio_image", "547604767a09773a29269153feed81ad6fa988aaa7689d1d2de99ab30ff8cef3"),
  ("importfrom:prepare_image", "0613f76e4dcd852b2f99c59ad42259ea9fa46ef63d0488c64994cc4ea78fbbdb"),
  ("importfrom:verify_control", "f1059e45783d44c550ce43100c8636957e6bf70957857a855b78fb8f6c6f41b3"),
  ("assign:KERNEL", "d43be1aeaec2d01deb92ea683f65ca509320dc965835251c117f65a508a5456e"),
  ("assign:PREFIX", "6f7cf1fde2f300c694980248cf5deac74c057699e3b66209c99d6b16a3c8fb6c"),
  ("assign:E_SHA256", "6fa026fd057647957099b64df038b39ef724dc7299405b2612233da500985be8"),
  ("assign:E_BYTES", "a00400913727d622c3b7d863c6b4658c7766751119461ef6b1cad8ac0ede6470"),
  ("assign:EARLY_SHA256", "d466ad2424cbc3e1201197c048ec3b55b916f22fa1db5bbec35975bc09415ef7"),
  ("assign:MAIN_SHA256", "261166cf71191abbd55c2eed7145f9c0a08cfdcdb4333258822007aa640ab80c"),
  ("assign:EARLY_BYTES", "bd1293183fb72525eca9529ac5ccdd2a7a2c0a20f254f758a20b2f002ed81cc8"),
  ("assign:MAIN_BYTES", "6398bd5fc272ed92a12c23e8b0afa87bfab3fabc8459218d2e2aad91ed688ae8"),
  ("assign:PAYLOAD_SHA256", "71c206105bafe5aa6dba886abc1984dc296249535e0b8fba32619f2f851182fd"),
  ("assign:PAYLOAD_BYTES", "8a89610af6edcf9ec40ab7231656da06b362521e9b4dcad38c60daaea5a25bec"),
  ("assign:INDEX_SHA256", "e4a5664c8faf1ca9f65decd3bc3c95cf85ddc2672c7f737e59a5ead6b6d1e981"),
  ("assign:GENERATED_SHA256", "5398a8ed5987928e25419751bd65e35af4c6a7b0220ce10994c39323e94af67d"),
  ("assign:HISTORICAL_BYTES", "6ada7d0e945b20185320744465670662ea495bd67c436b2ea0d3ed800365c907"),
  ("assign:DUMP_SHA256", "25c7ef076755aa10ea566701cffeca7edb4f3f2de252ce091475c87cff71c317"),
  ("assign:DUMP_BYTES", "0b10f945f6413c821ca7a9cbc69d85191be3ac198485aa1626f5165dc144755b"),
  ("assign:INDEX_INPUT_SHA256", "45a46d529b7625dec1f28b5322a6b04ad09c0fc1d66979d1c030ceb030e7de15"),
  ("assign:ALIASES", "f197d66c7c3158945c2a703d91f6ab3fbacfe3fc5c75db1f587ff32338f39f20"),
  ("assign:EXPORTS", "c9975a39f5b68012060a93ee83a324650227cb1b1a2de45e94b5e782bdee91fb"),
  ("assign:CONTROL_ROOT", "a01bc10505d1816cb39254e22e5e250656aeac27799c05d5e203f8cf516b27ce"),
  ("assign:LOOKUP_ROOT", "ab3e491d594814136dc18ede121c2c41a3c93527ddbed326fa9fc9fe756e5de8"),
  ("assign:EMPTY_CONFIG", "83c1d997c88cb4d2050f5af81d94d1145ff9e96cffcbcce8aad39a0e28599baf"),
  ("assign:EARLY_PATH", "45f5896cf0e0e8553cee5b5bfc96dc84e7c38ad386117ab54e20a30b69ed25ab"),
  ("assign:MAIN_PATH", "0c8aa2c8a63e996582eb05c1adf7a99848ab7c07b520a05bdaf4895d148a4604"),
  ("assign:MAX_INDEX_BYTES", "f284e719f76e0499825194137133c2cebd5e245d78a243d35892ce8661883888"),
  ("assign:MODULE_MODEL_SHA256", "ef773dc100cac3f3e294134ff25b852873aa8c9fc91b52a1780c89ec6ac783eb"),
  ("assign:STRUCTURAL_BINDINGS", "4ea5bb1da9f74844ac04e4df4a7a5b4124dfe67d66f4ace1fc401d5e204b9c79"),
  ("assign:STRUCTURAL_RECORD_ROOT", "1b17b09a6098265d7b28c9949009f77ef72628ea72cf03167dca886f6df07a88"),
  ("assign:STRUCTURAL_ARTIFACTS", "5d6e8c484fad13af7bd73f13a0d8b4755155f22cdeca0ad16a53439e28e35580"),
  ("assign:REAL_OPERATIONAL_ARTIFACTS", "8b39409fb8edc56dbddafbd9edfa3403303a9390383a8e0f1eafa399ab669e1f"),
  ("assign:STDOUT_BYTES", "74ab8a82808e6823d1b1701007b81af4421513e0873a17e84de72b71107b6993"),
  ("assign:STDERR_BYTES", "993555f7ce3478dfe78dca84ab05e2c08e10450b735377c34943ce7b6de5da09"),
  ("assign:REPORT_BYTES", "47c75e35904ce0a32984ed8711fc61af8a7d0d7829083e2fd58692d85c190da0"),
  ("assign:SEMANTIC_RECORDS", "0800746de7c235d429c5f766e880a572a36c0e5ee17f0c574232c3d80698c002"),
  ("assign:SEMANTIC_FIXTURE_PATHS", "7f611206c65213a2043afe70012f4fbf41bd13335db7e1a052dfd14a279b181f"),
  ("assign:SEMANTIC_OPERATIONAL_PATHS", "0b2cf08e2d0fce6277df06d227f1e880e7dbf66aecb2fc21c129650f40dafce6"),
  ("assign:SEMANTIC_FIXTURE_PENDING", "a6fc0c212689d3a34a08b67f7e7062d8e5a3d79b966f132a83b49c975c3b3427"),
  ("assign:SEMANTIC_FIXTURE_RESULT", "74d9b0216f33e105714a48b554e7476b62de49a152df11d5ff4511088ac0b018"),
  ("assign:SEMANTIC_FIXTURE_WORK_MEMBERS", "300008ecd907d464de24a57701183b166adfba55ffd1e4c5bc9c1400ee335084"),
  ("assign:ARCHIVE_OBSERVATIONS", "c75f4cf2097925fca79cb8a505415a097c6f7d399c6c593c19aeebeb32746939"),
  ("assign:SEMANTIC_REPORT_KEYS", "3fe4f81b1273dc5e18678d2cc32f149ef26d7e3791a38e435bd7fe14d959ddec"),
  ("assign:SEMANTIC_FILE_KEYS", "7645a58bc23ea3e7f6846895746f1557ed3f4b7318993bacb980668904593ed1"),
  ("assign:SEMANTIC_DIRECTORY_KEYS", "20d27bb5e346aa3badee9d1946e54f2291b3ffcb615fe8d62b860c21d82e398c"),
  ("assign:SEMANTIC_TREE_FILE_KEYS", "cd913f39abef588c82658aeb07f17981947e80247d2dcc6e4f27d358c272fd93"),
  ("assign:RENAME_NOREPLACE", "a74ee274780db4b4c058ebbed176aba5f4dc138caa59ebdf14f627a091fed571"),
  ("assign:_AT_FDCWD", "e4936dede418888c857a0624d67aed46af0dc659289b83ce6738e5a11fab36a1"),
  ("class:RecipeError", "87913eb4f3baf74914bf2129034907b02229cd20ebd124b197c34cc33b695cac"),
  ("class:ESelection", "ba11d47b8db628fdad11676b9b44f3a8cedda76825f0fa5cabf29f34e496b2e4"),
  ("class:Regeneration", "7f0c6f5abf42f1f7abf943f7a4fe66846ffbd2695097dd74b62ef690eaadc942"),
  ("class:StructuralPolicy", "0a1fbf0ad268376815c5fdc92fdb737cfb6278d637e87769fcb251fc6e997d67"),
  ("class:StructuralAcceptance", "8b60ef703463e1c9f5d76eac1008371608cef450bb46e7de557edb142d733511"),
  ("class:RawControlFiles", "04dd48b54d10dda7e6b8933157533fe76be1b72e5dc8d7fc1bcbcef1dc8c6c18"),
  ("class:MappedControlOutputs", "4effe0f46f2ce2e94ebad694929d6e95c177537bfc9daee6122215a86fd17459"),
  ("class:SemanticFixtureEvaluation", "5b4baca00344584870b955bef9fb31749d12c12d1f616af9ca7c510978aeceda"),
  ("class:SemanticFixtureAcceptance", "1653442d227b73238acc67d460409200eac91d6e4e9266d768a71254d33d5969"),
  ("function:_require", "c8a3e0301ecaff95210f9c2a109b1e531f93d13b9879f6a6d1c6a9236273a48d"),
  ("function:_sha256", "9d245004e81cc17da8e38e2c6aa6acbea39d785a236e866700bcc6827a3ed063"),
  ("function:_validated_names", "6c32523fbfaf9d83ce5f945dbbee6ee75ec232601e53bb7327ba9e2505d28e51"),
  ("function:select_e", "be3a4fff7981ef794d757694286eeb66789053830f6b9aca8d668901757e6ba3"),
  ("function:validate_regeneration", "4758bd16562b2cf3a59b607f4d431e06c627d18ed899ead3a275734a39ce24fe"),
  ("function:_probe", "17a7ad1bc0abec25c286c61dbd17b9781657133fe5953d0de61e6e22c6ecf29a"),
  ("function:command_plan", "0b94861ea2bb609101a45e5f8f4951d494fd8f9b55b60cf8b569004b0fdfe5c9"),
  ("function:_structural_identity", "7ca98213cb6787d1aa093a43fa2f51a9e873bda68d0f67f9baedd6db7d167fb4"),
  ("function:_structural_read", "7bccef667a69cb992d94bd0f02c6c528944cb9f5f109820e1afcbd409988fd35"),
  ("function:_structural_json", "e8ac82d719311cd2defa0029e07cd4f1ed644130bb8eb5fd49c6ec5e5376c3e0"),
  ("function:_structural_record", "51b5fd31ceb33ced2c2a4867e578a037ad5e94d81462f0ce70628e112e03f7cf"),
  ("function:_structural_commands", "67972235fe9ef9d1c2d4f7acff3cd0a800aa01137c79d0f45494090947024ebe"),
  ("function:structural_policy", "aee5c1fe2334bc0c1cb57f2121512a93717d435ab7ae42028a5f7aef3a69ab8d"),
  ("function:_collect_fixed_raw_files", "b4b4348ca1b2be21f42496f59749c0f4fce04f9891c3ce4485db6b5cffd2e28d"),
  ("function:_map_raw_control_outputs", "78c5be4e8e9cb510d5a47fcef52be304c4e6b7662a2319b83fe14e7396571b02"),
  ("function:_read_fixed_semantic_fixture_outputs", "debb6d829a2a92206175db9b56ace4ad89b39473a6efbe43cbb28a384f0837f2"),
  ("function:_read_fixed_operational_outputs", "bce85002d8bd1101592cc1383ec63e445901b4e7d930d8a12d67d9ee0dca6a34"),
  ("function:_semantic_json", "5f45a69954d8c3113d32a1a9ccabd83526bbe5f631d0f7b18263abda3b7784b3"),
  ("function:_semantic_json_bytes", "16b3bc659908e85172d19666fbed6606786fa40b7f1a8d82e8f72ac8b7a50593"),
  ("function:_semantic_module_names", "fd8bf3ebb5ecace6237b8c37d249401ae952f32953de54e5d7eb4e5c1e1be58a"),
  ("function:_semantic_generated_relative", "b994c099c210592d354a1f1564f41a1f91d38c13c4fd4b34a863477f267fba33"),
  ("function:_semantic_control_before", "21ed89e5d92a44df2b571640a954c8d4ff826e31a47ce3644f129306cf7b8041"),
  ("function:_semantic_dependencies", "7bab3b44f2ea43760ed2098dbd3bcae5dc5f5d5124c6f9aa6260ac69aeada156"),
  ("function:_semantic_expected_module", "3cbc32958ada166569919159657caf41ee59586b7bc2ea6270db20688e1042aa"),
  ("function:_semantic_lookup_target", "f1f355fbf1aa28764fffd119cd3be3155f177261a4839fa2c7269179f76526a8"),
  ("function:_semantic_file_observation", "373c660d7136f5c0b82c785937f0f677a8522e90f0a89603b9ced3d22233f77a"),
  ("function:_semantic_stable_file", "b40ef5c95ddb2f3f8c4c9532b2d9c6f1e4c9dd0f0daee4a22808b9b2e02f4b13"),
  ("function:_semantic_stable_tree", "c75ab3a2e3d16897628c4b5031b82b74f0e2cb5c1417160bc467a0972ef06a1f"),
  ("function:_semantic_tree_identity_records", "71cf7060623e0cebe53319393878a8b49116b504ae79b48bd23d7d0bcdfa579a"),
  ("function:_semantic_expected_provenance", "bda312f6e25f355c55f94397961657fb6b466e7dd9444af26f12fb67a51f39a0"),
  ("function:_semantic_provenance", "5690fe985b2a722cbbbaaba88662def5aa2ecf55d559499474e7ac0dcecbdc0e"),
  ("function:_semantic_command_plan", "a84fce839316e43f5e8578dc62311d54ef0a1c649c71f5ee73ccf20a24105e54"),
  ("function:_semantic_command_observation", "b6e315c79f55c619581814507bc08799eb4afc8036743e90bbd1847f6419f387"),
  ("function:_semantic_identity_records", "fd125fbf978e706f8db088c5020f104e80bdab36ebf2e4f234b4207c64a89627"),
  ("function:_semantic_bound_observation", "9714413167510e0cfe8607247c66e76dc5c1e0622157491cdb7c9cdff110d830"),
  ("function:_semantic_archive_records", "630968c9723a8e894690c3cc3b0b7b10560af477a9227b8b8a679c15a022e483"),
  ("function:_semantic_aggregate", "5b6ff7819d4119034ed6daea4ea5afe1bd0846efbcdb53cbeeb91c71957f5dde"),
  ("function:_validate_file_metadata", "9d36cd1ff10327e9e8855e262d898edff5eee27baadeffccacbc23b6078ced67"),
  ("function:_validate_file_content", "9505e713f4625b185e30d100d8199d049db609bc25a70a2f16aa686359baae29"),
  ("function:_validate_command_shape", "0859adc261782c7978b48b04c07e2de29a5cce3ca5615ca565558c5f538afc7b"),
  ("function:_validate_archive_observation", "01f9b670880cfcef009f63559f073dc04265c3ab3bbd3a51a3955bd1808fd829"),
  ("function:_validate_payload_observation", "2e183fc75c0a9af25af7f6a6a888ddac548d2eb0bd639dd6f691689c0db481c4"),
  ("function:_validate_tree_observation", "a7633a0ef55ff45ceb9435e8f8a1d1c89d79e3653b3d7c10655bf4116c949764"),
  ("function:_validate_index_observation", "da34cd7f2ef07c80afb7daa68a14b1cd541c7425b3ad1f855bc41d6e414b88cf"),
  ("function:_validate_module_observation", "94f64697e9903a82ba8c8100e68d0fd6d786b141b5c73eea6d01749f764a52b9"),
  ("function:_validate_alias_observation", "1d2476e2aee9e8ef51b47d06b8789205a6632de8cd2ea1dd542670fffe2e02b6"),
  ("function:_validate_symbol_observation", "6bcdeef980eb334aa022f4c3b4c190363e2d404f96febfb0a5d44fc43e19c095"),
  ("function:_validate_command_observation", "4cf5753ce6aa207dd8c3e73c0c31fba06c34cb76edf21c6af3451192f197a728"),
  ("function:_validate_identity_observation", "bad4e145516e622630b4920819700cc740046b6a3d0426bf70fd1bf6c2e22c40"),
  ("function:_validate_provenance_observation", "9942a8b7424b51256a638e6a5717a1660cbc1941680e5051214f939ded1bc6c2"),
  ("function:_validate_archive_family", "21e193e507d53290b0f7b5984b5fd9c7558ef4710739abd607f039c49059438e"),
  ("function:_validate_payload_family", "b741188b02226a136474819be60e83bc63be206cdaea3c9876d4d4476601b264"),
  ("function:_validate_tree_family", "9b31b4119e0e94e76087942aaeb829f4f59028d4a3e504b3b0db0c457ad3b9e5"),
  ("function:_validate_index_family", "7bc9cb83102e2045d896b685f748f83f5b85623c6e3d58b2dd2407dda27cb372"),
  ("function:_validate_module_family", "ef3554bc6b739672eb71169a6f2ee6016478745e9ccc88b0768cafe59cf9244e"),
  ("function:_validate_alias_family", "b8dec1a227837017d34ec2736b1ff0d97e33cad3caa0bb6324f26a7441a8dfcd"),
  ("function:_validate_symbol_family", "26392710d0ace0601d962b2c7890102a6b012f0a955a9f6eecb79f44357e5ae0"),
  ("function:_validate_command_family", "6b180629b5e1b3d4d8796e4536f5343a34852a4f24ce1ba437adb37a8ff91c89"),
  ("function:_validate_identity_family", "4ee09a4c3bd616376f265ce651ee78d4072fa30c34f167507217f9cf4b133eff"),
  ("function:_validate_provenance_family", "573edfdf0da77b1c2b5dc32f9cc198d4264a179cf3738743af27b4c59e7b896f"),
  ("function:_evaluate_control_semantics", "419e7a36ae540f852bd72a2977a5c5853e188bb32dc2436234e93075f792f1a0"),
  ("function:_rename_noreplace_errcheck", "d5f226b091a69055febe5a23cae629b29af5bb28d8903abea3754a3efa3945bf"),
  ("assign:_SEMANTIC_LIBC", "7428666797d2cb5b97661440f4c11bf97189f7e18f8783401a851a4af82e9ef0"),
  ("assign:_SEMANTIC_LIBC.renameat2.argtypes", "96162c6bd7154053244bb1667cba13bfcadd86713d5aa95cb122679162a76a96"),
  ("assign:_SEMANTIC_LIBC.renameat2.restype", "4c3f37aed312fb2c30e4ebc2a57afb241b28fa342fb618cb984f70a11c55407a"),
  ("assign:_SEMANTIC_LIBC.renameat2.errcheck", "4df426cb6c947ce2d5628880c71bc58f49decd790f7ba44d96b26320a412a29e"),
  ("function:_rename_noreplace", "0d8b2e4a364183664265ea87c5ef90cecf3503108bfcae65eb98631d7a9d07a6"),
  ("function:_semantic_fixture_work_membership", "0e6d39c11477f3b22a09435abe41f17a29d1418e9ff69209480c11d3fc4247db"),
  ("function:_semantic_fixture_result_bytes", "8053ddd55a7366843ab0ac7e4eaf129d8e4d388036ac95cb5a6dc01ebf3c1013"),
  ("function:publish_semantic_fixture_result", "a2bfb6e5b2e8133c2d7f318a6860cde99a465a490296ee344a5fff1ca30d0d73"),
  ("function:operational_policy", "b6e7c293abcf0a790f80b4b5a271321199c4f008c71bcefd89e0fcd054073854"),
  ("function:finalize_operational_result", "95f93cd8a8ccd67b418dcb03b1701ec686f08e06f805dcd7da1e1dcc2db2468d"),
  ("function:finalize_structural_result", "b9134fb21410042da05a0f1193980a4d7871cecd56ab80e75de8328baf7f57d0"),
  ("function:main", "b598e4e99d0978fe413f32fa3b4f241a40dc3ec6b4d7627fcf6fb9b9d2cf549d"),
  ("guard:main", "3340fd16ba41ba1ddf3989cd136a498b72a97f7796e0f7fad6e815585dbc1c52"),
)

FUTURE_EARLY_TEMPLATE = '''
FIXED_SOURCE_BYTES = 128 * 1024
FIXED_SOURCE_INPUTS = (
  ("cpio_image", "/inputs/helper/cpio_image.py", "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58"),
  ("verify_control", "/inputs/control/verify_control.py", "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8"),
  ("prepare_image", "/inputs/assembly/prepare_image.py", "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60"),
  ("t1_image_contract", "/inputs/contract/image_contract.py", "a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf"),
  ("e_control", "/inputs/subject/e_control.py", "16016875e731e88d047eb805c7c6d03045300abdb262361b18010a952adb7b80"),
)

def _fixed_source_identity(info: os.stat_result) -> tuple[int, ...]:
  return (
    info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
    info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns,
  )

def _load_fixed_source(name: str, path: str, digest: str) -> object:
  source = Path(path)
  _require(name not in os.sys.modules, "E_CONTROL_SOURCE_INVALID")
  before = source.lstat()
  _require(stat.S_ISREG(before.st_mode), "E_CONTROL_SOURCE_INVALID")
  _require(stat.S_IMODE(before.st_mode) == 0o600, "E_CONTROL_SOURCE_INVALID")
  _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_SOURCE_INVALID")
  _require(before.st_nlink == 1, "E_CONTROL_SOURCE_INVALID")
  _require(0 < before.st_size <= FIXED_SOURCE_BYTES, "E_CONTROL_SOURCE_INVALID")
  descriptor = os.open(
    source, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
  )
  with os.fdopen(descriptor, "rb") as stream:
    _require(
      _fixed_source_identity(before) == _fixed_source_identity(os.fstat(descriptor)),
      "E_CONTROL_SOURCE_INVALID",
    )
    raw = stream.read(FIXED_SOURCE_BYTES + 1)
    _require(
      _fixed_source_identity(before) == _fixed_source_identity(os.fstat(descriptor))
      == _fixed_source_identity(source.lstat()),
      "E_CONTROL_SOURCE_INVALID",
    )
  _require(len(raw) == before.st_size <= FIXED_SOURCE_BYTES, "E_CONTROL_SOURCE_INVALID")
  _require(hashlib.sha256(raw).hexdigest() == digest, "E_CONTROL_SOURCE_INVALID")
  module = type(os)(name)
  module.__file__ = str(source)
  os.sys.modules[name] = module
  exec(compile(raw, str(source), "exec"), module.__dict__)
  return module

def _bootstrap_fixed_sources() -> None:
  saved_path = tuple(os.sys.path)
  saved_modules = dict(os.sys.modules)
  try:
    try:
      assembly = _load_fixed_source(*FIXED_SOURCE_INPUTS[2])
      _require(
        assembly.__file__ == FIXED_SOURCE_INPUTS[2][1]
        and os.sys.modules["verify_control"].__file__ == FIXED_SOURCE_INPUTS[1][1]
        and os.sys.modules["cpio_image"].__file__ == FIXED_SOURCE_INPUTS[0][1],
        "E_CONTROL_SOURCE_INVALID",
      )
      _load_fixed_source(*FIXED_SOURCE_INPUTS[3])
      _load_fixed_source(*FIXED_SOURCE_INPUTS[4])
    except Exception:
      os.sys.modules.clear()
      os.sys.modules.update(saved_modules)
      raise
  finally:
    os.sys.path[:] = saved_path

_bootstrap_fixed_sources()
'''

FUTURE_LATE_TEMPLATE = '''
@dataclass(frozen=True)
class ExecutionPolicy:
  command: tuple[str, ...]
  environment: tuple[tuple[str, str], ...]
  task_bindings: tuple[str, ...]
  uid: int
  gid: int
  cwd: str
  umask: int
  runtime_mounts: int
  fixed_sandbox_mounts: int
  task_inputs: int
  read_only_mounts: int
  planned_children: int
  control_seconds: float
  child_seconds: float
  workload_seconds: int
  outer_seconds: int
  mode: str

EXECUTION_COMMAND = ("/usr/bin/python3.14", "-I", "-S", "-B", "/inputs/recipe")
EXECUTION_ENVIRONMENT = (
  ("PATH", "/usr/bin:/bin"),
  ("LC_ALL", "C"),
  ("TMPDIR", "/tmp"),
  ("PYTHONDONTWRITEBYTECODE", "1"),
)
EXECUTION_TASK_BINDINGS = (
  "/inputs/recipe", "/inputs/subject", "/inputs/contract", "/inputs/assembly",
  "/inputs/control", "/inputs/helper", "/inputs/base", "/inputs/index-inputs",
)
EXECUTION_UID = 1001
EXECUTION_GID = 1001
EXECUTION_CWD = "/work"
EXECUTION_UMASK = 0o077
EXECUTION_RUNTIME_MOUNTS = 582
EXECUTION_FIXED_SANDBOX_MOUNTS = 3
EXECUTION_TASK_INPUTS = 8
EXECUTION_READ_ONLY_MOUNTS = 593
EXECUTION_PLANNED_CHILDREN = 424
EXECUTION_CONTROL_SECONDS = 270.0
EXECUTION_CHILD_SECONDS = 30.0
EXECUTION_WORKLOAD_SECONDS = 280
EXECUTION_OUTER_SECONDS = 285
EXECUTION_MODE = "E_NO_CHANGE_OFFLINE"
OPERATIONAL_RECORD_ROOT = "/work/e-control-children-e1"
OPERATIONAL_STDOUT_LIMITS = (
  1024, 1024, 65536, 65536, E_BYTES - 10240,
  1213760, 12368, 66512, 20312, 1, 128 * 1024, 128 * 1024,
  *((4096, 65536) * 200),
  *((65536,) * 12),
)
OPERATIONAL_STDERR_LIMIT = 1
OPERATIONAL_REPORT_LIMIT = 128 * 1024
OPERATIONAL_EMPTY_CONFIG_LIMIT = 1
OPERATIONAL_EARLY_STREAM_LIMIT = 10240
OPERATIONAL_MAIN_STREAM_LIMIT = 61286668
OPERATIONAL_RECORD_FILES = 1272
OPERATIONAL_CONTROL_TREE_FILES = 214
OPERATIONAL_LOOKUP_TREE_FILES = 207
OPERATIONAL_TREE_DIRECTORIES = 48
OPERATIONAL_TREE_MAX_DEPTH = 16
OPERATIONAL_TREE_FILE_LIMIT = 2 * 1024 * 1024
OPERATIONAL_TREE_AGGREGATE_LIMIT = 64 * 1024 * 1024

def operational_execution_policy() -> ExecutionPolicy:
  return ExecutionPolicy(
    command=EXECUTION_COMMAND,
    environment=EXECUTION_ENVIRONMENT,
    task_bindings=EXECUTION_TASK_BINDINGS,
    uid=EXECUTION_UID,
    gid=EXECUTION_GID,
    cwd=EXECUTION_CWD,
    umask=EXECUTION_UMASK,
    runtime_mounts=EXECUTION_RUNTIME_MOUNTS,
    fixed_sandbox_mounts=EXECUTION_FIXED_SANDBOX_MOUNTS,
    task_inputs=EXECUTION_TASK_INPUTS,
    read_only_mounts=EXECUTION_READ_ONLY_MOUNTS,
    planned_children=EXECUTION_PLANNED_CHILDREN,
    control_seconds=EXECUTION_CONTROL_SECONDS,
    child_seconds=EXECUTION_CHILD_SECONDS,
    workload_seconds=EXECUTION_WORKLOAD_SECONDS,
    outer_seconds=EXECUTION_OUTER_SECONDS,
    mode=EXECUTION_MODE,
  )

def _read_bounded_operational_file(path: Path, limit: int) -> bytes:
  _require(path.is_absolute(), "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(limit) is int, "E_CONTROL_OPERATIONAL_INVALID")
  _require(0 < limit <= OPERATIONAL_TREE_AGGREGATE_LIMIT, "E_CONTROL_OPERATIONAL_INVALID")
  before = path.lstat()
  _require(stat.S_ISREG(before.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
  _require(stat.S_IMODE(before.st_mode) == 0o600, "E_CONTROL_OPERATIONAL_INVALID")
  _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
  _require(before.st_nlink == 1, "E_CONTROL_OPERATIONAL_INVALID")
  _require(0 <= before.st_size <= limit, "E_CONTROL_OPERATIONAL_INVALID")
  descriptor = os.open(
    path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
  )
  with os.fdopen(descriptor, "rb") as stream:
    _require(
      _structural_identity(before) == _structural_identity(os.fstat(descriptor)),
      "E_CONTROL_OPERATIONAL_INVALID",
    )
    raw = stream.read(limit + 1)
    _require(
      _structural_identity(before) == _structural_identity(os.fstat(descriptor))
      == _structural_identity(path.lstat()),
      "E_CONTROL_OPERATIONAL_INVALID",
    )
  _require(len(raw) == before.st_size <= limit, "E_CONTROL_OPERATIONAL_INVALID")
  return raw

def _operational_record_path(index: int, suffix: str) -> Path:
  _require(type(index) is int and 0 <= index < SEMANTIC_RECORDS,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(suffix) is str and suffix in ("stdout", "stderr", "json"),
           "E_CONTROL_OPERATIONAL_INVALID")
  return Path(OPERATIONAL_RECORD_ROOT) / f"child-{index:03d}.{suffix}"

def _validate_operational_record_root() -> TreeState:
  root = Path(OPERATIONAL_RECORD_ROOT)
  _require(root.is_absolute(), "E_CONTROL_OPERATIONAL_INVALID")
  before = root.lstat()
  _require(stat.S_ISDIR(before.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
  _require(stat.S_IMODE(before.st_mode) == 0o700, "E_CONTROL_OPERATIONAL_INVALID")
  _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
  _require(before.st_nlink == 2, "E_CONTROL_OPERATIONAL_INVALID")
  expected = {
    f"child-{index:03d}.{suffix}"
    for index in range(SEMANTIC_RECORDS)
    for suffix in ("stdout", "stderr", "json")
  }
  observed = {}
  descriptor = os.open(
    root, os.O_RDONLY | os.O_DIRECTORY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
  )
  try:
    _require(_structural_identity(before) == _structural_identity(os.fstat(descriptor)),
             "E_CONTROL_OPERATIONAL_INVALID")
    with os.scandir(descriptor) as entries:
      for entry in entries:
        info = entry.stat(follow_symlinks=False)
        _require(stat.S_ISREG(info.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
        _require(stat.S_IMODE(info.st_mode) == 0o600, "E_CONTROL_OPERATIONAL_INVALID")
        _require(info.st_uid == info.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
        _require(info.st_nlink == 1, "E_CONTROL_OPERATIONAL_INVALID")
        observed[entry.name] = info
        _require(len(observed) <= OPERATIONAL_RECORD_FILES,
                 "E_CONTROL_OPERATIONAL_INVALID")
    _require(
      _structural_identity(before) == _structural_identity(os.fstat(descriptor))
      == _structural_identity(root.lstat()),
      "E_CONTROL_OPERATIONAL_INVALID",
    )
  finally:
    os.close(descriptor)
  _require(set(observed) == expected, "E_CONTROL_OPERATIONAL_INVALID")
  _require(len(observed) == OPERATIONAL_RECORD_FILES, "E_CONTROL_OPERATIONAL_INVALID")
  files = {}
  for index in range(SEMANTIC_RECORDS):
    for suffix, limit in (
      ("stdout", OPERATIONAL_STDOUT_LIMITS[index]),
      ("stderr", OPERATIONAL_STDERR_LIMIT),
      ("json", OPERATIONAL_REPORT_LIMIT),
    ):
      path = _operational_record_path(index, suffix)
      raw = _read_bounded_operational_file(path, limit)
      _require(_structural_identity(observed[path.name]) == _structural_identity(path.lstat()),
               "E_CONTROL_OPERATIONAL_INVALID")
      files[path.name] = FileState(_structural_identity(observed[path.name]), _sha256(raw))
  _require(_structural_identity(before) == _structural_identity(root.lstat()),
           "E_CONTROL_OPERATIONAL_INVALID")
  return TreeState({".": _structural_identity(before)[:5]}, files)

def _bounded_operational_tree(
  root: Path,
  *,
  expected_files: int,
  expected_directories: int,
  max_depth: int,
  per_file_limit: int,
  aggregate_limit: int,
) -> TreeState:
  _require(isinstance(root, Path) and root.is_absolute(), "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(expected_files) is int and 0 <= expected_files <= 4096,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(expected_directories) is int and 1 <= expected_directories <= 512,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(max_depth) is int and 0 <= max_depth <= OPERATIONAL_TREE_MAX_DEPTH,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(per_file_limit) is int and 0 < per_file_limit <= OPERATIONAL_TREE_FILE_LIMIT,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(aggregate_limit) is int and 0 < aggregate_limit <= OPERATIONAL_TREE_AGGREGATE_LIMIT,
           "E_CONTROL_OPERATIONAL_INVALID")
  root_before = root.lstat()
  pending = [(root, 0, _structural_identity(root_before))]
  directories = {}
  files = {}
  aggregate = 0
  while pending:
    directory, depth, expected_identity = pending.pop()
    _require(depth <= max_depth, "E_CONTROL_OPERATIONAL_INVALID")
    before = directory.lstat()
    _require(_structural_identity(before) == expected_identity,
             "E_CONTROL_OPERATIONAL_INVALID")
    _require(stat.S_ISDIR(before.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
    _require(stat.S_IMODE(before.st_mode) == 0o700, "E_CONTROL_OPERATIONAL_INVALID")
    _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
    relative_directory = "." if directory == root else str(directory.relative_to(root))
    directories[relative_directory] = _structural_identity(before)[:5]
    _require(len(directories) <= expected_directories, "E_CONTROL_OPERATIONAL_INVALID")
    descriptor = os.open(
      directory,
      os.O_RDONLY | os.O_DIRECTORY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
      _require(_structural_identity(before) == _structural_identity(os.fstat(descriptor)),
               "E_CONTROL_OPERATIONAL_INVALID")
      with os.scandir(descriptor) as entries:
        for entry in entries:
          info = entry.stat(follow_symlinks=False)
          path = directory / entry.name
          if stat.S_ISDIR(info.st_mode):
            _require(stat.S_IMODE(info.st_mode) == 0o700, "E_CONTROL_OPERATIONAL_INVALID")
            _require(info.st_uid == info.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
            pending.append((path, depth + 1, _structural_identity(info)))
            _require(len(directories) + len(pending) <= expected_directories,
                     "E_CONTROL_OPERATIONAL_INVALID")
          else:
            _require(stat.S_ISREG(info.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
            _require(stat.S_IMODE(info.st_mode) == 0o600, "E_CONTROL_OPERATIONAL_INVALID")
            _require(info.st_uid == info.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
            _require(info.st_nlink == 1, "E_CONTROL_OPERATIONAL_INVALID")
            raw = _read_bounded_operational_file(path, per_file_limit)
            _require(_structural_identity(info) == _structural_identity(path.lstat()),
                     "E_CONTROL_OPERATIONAL_INVALID")
            aggregate += len(raw)
            _require(aggregate <= aggregate_limit, "E_CONTROL_OPERATIONAL_INVALID")
            relative_file = str(path.relative_to(root))
            files[relative_file] = FileState(_structural_identity(info), _sha256(raw))
            _require(len(files) <= expected_files, "E_CONTROL_OPERATIONAL_INVALID")
      _require(
        _structural_identity(before) == _structural_identity(os.fstat(descriptor))
        == _structural_identity(directory.lstat()),
        "E_CONTROL_OPERATIONAL_INVALID",
      )
    finally:
      os.close(descriptor)
  _require(len(files) == expected_files, "E_CONTROL_OPERATIONAL_INVALID")
  _require(len(directories) == expected_directories, "E_CONTROL_OPERATIONAL_INVALID")
  return TreeState(directories, files)

def _collect_operational_outputs() -> RawControlFiles:
  record_state = _validate_operational_record_root()
  records = []
  for index in range(SEMANTIC_RECORDS):
    stdout = _read_bounded_operational_file(
      _operational_record_path(index, "stdout"), OPERATIONAL_STDOUT_LIMITS[index],
    )
    stderr = _read_bounded_operational_file(
      _operational_record_path(index, "stderr"), OPERATIONAL_STDERR_LIMIT,
    )
    report = _read_bounded_operational_file(
      _operational_record_path(index, "json"), OPERATIONAL_REPORT_LIMIT,
    )
    records.append((stdout, stderr, report))
  control_state = _bounded_operational_tree(
    Path(CONTROL_ROOT),
    expected_files=OPERATIONAL_CONTROL_TREE_FILES,
    expected_directories=OPERATIONAL_TREE_DIRECTORIES,
    max_depth=OPERATIONAL_TREE_MAX_DEPTH,
    per_file_limit=OPERATIONAL_TREE_FILE_LIMIT,
    aggregate_limit=OPERATIONAL_TREE_AGGREGATE_LIMIT,
  )
  lookup_state = _bounded_operational_tree(
    Path(LOOKUP_ROOT),
    expected_files=OPERATIONAL_LOOKUP_TREE_FILES,
    expected_directories=OPERATIONAL_TREE_DIRECTORIES,
    max_depth=OPERATIONAL_TREE_MAX_DEPTH,
    per_file_limit=OPERATIONAL_TREE_FILE_LIMIT,
    aggregate_limit=OPERATIONAL_TREE_AGGREGATE_LIMIT,
  )
  empty_config_raw = _read_bounded_operational_file(
    Path(EMPTY_CONFIG), OPERATIONAL_EMPTY_CONFIG_LIMIT,
  )
  early_raw = _read_bounded_operational_file(Path(EARLY_PATH), OPERATIONAL_EARLY_STREAM_LIMIT)
  main_raw = _read_bounded_operational_file(Path(MAIN_PATH), OPERATIONAL_MAIN_STREAM_LIMIT)
  return RawControlFiles(
    paths=SEMANTIC_OPERATIONAL_PATHS,
    record_state=record_state,
    records=tuple(records),
    control_state=control_state,
    lookup_state=lookup_state,
    empty_config_raw=empty_config_raw,
    early_raw=early_raw,
    main_raw=main_raw,
  )
'''


def top_level_label(node: ast.stmt) -> str:
  if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
      and isinstance(node.value.value, str):
    return "expr:docstring"
  if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) \
      and isinstance(node.value.func, ast.Name):
    return f"call:{node.value.func.id}"
  if isinstance(node, ast.Import):
    return "import:" + ",".join(alias.name for alias in node.names)
  if isinstance(node, ast.ImportFrom):
    return "importfrom:" + str(node.module)
  if isinstance(node, ast.Assign) and len(node.targets) == 1:
    return "assign:" + ast.unparse(node.targets[0])
  if isinstance(node, ast.ClassDef):
    return "class:" + node.name
  if isinstance(node, ast.FunctionDef):
    return "function:" + node.name
  if isinstance(node, ast.If):
    return "guard:main"
  return "invalid:" + type(node).__name__


def normalized_node_dump(node: ast.stmt) -> str:
  return ast.dump(node, include_attributes=False)


def node_manifest(nodes: list[ast.stmt]) -> tuple[tuple[str, str], ...]:
  return tuple(
    (top_level_label(node), hashlib.sha256(normalized_node_dump(node).encode()).hexdigest())
    for node in nodes
  )


def future_nodes(source: str) -> list[ast.stmt]:
  return ast.parse(source, filename="<e-control-execution-reference>", mode="exec").body


def expected_future_manifest() -> tuple[tuple[str, str], ...]:
  standard = BASELINE_TOP_LEVEL_MANIFEST[:12]
  dependencies = BASELINE_TOP_LEVEL_MANIFEST[12:15]
  body = list(BASELINE_TOP_LEVEL_MANIFEST[15:-1])
  moved = (
    next(item for item in body if item[0] == "class:RecipeError"),
    next(item for item in body if item[0] == "function:_require"),
  )
  body = [item for item in body if item[0] not in {"class:RecipeError", "function:_require"}]
  insertion = next(index for index, item in enumerate(body)
                   if item[0] == "function:operational_policy")
  early = node_manifest(future_nodes(FUTURE_EARLY_TEMPLATE))
  late = node_manifest(future_nodes(FUTURE_LATE_TEMPLATE))
  return (
    *standard, *moved, *early, *dependencies, *body[:insertion], *late,
    *body[insertion:], BASELINE_TOP_LEVEL_MANIFEST[-1],
  )


FUTURE_TOP_LEVEL_MANIFEST = expected_future_manifest()
FUTURE_REFERENCE_DUMPS = {
  top_level_label(node): normalized_node_dump(node)
  for node in (*future_nodes(FUTURE_EARLY_TEMPLATE), *future_nodes(FUTURE_LATE_TEMPLATE))
}


OPERATIONAL_FULL_TOP_LEVEL_LABELS = (
  "expr:docstring", "importfrom:dataclasses", "import:ctypes", "import:errno",
  "importfrom:fnmatch", "import:hashlib", "import:json", "import:math", "import:os",
  "importfrom:pathlib", "import:re", "import:stat", "importfrom:typing",
  "class:RecipeError", "function:_require", "assign:FIXED_SOURCE_BYTES",
  "assign:FIXED_SOURCE_INPUTS", "function:_fixed_source_identity",
  "function:_load_fixed_source", "function:_bootstrap_fixed_sources",
  "call:_bootstrap_fixed_sources", "importfrom:cpio_image", "importfrom:prepare_image",
  "importfrom:verify_control", "importfrom:e_control", "assign:KERNEL", "assign:PREFIX",
  "assign:E_SHA256", "assign:E_BYTES", "assign:EARLY_SHA256", "assign:MAIN_SHA256",
  "assign:EARLY_BYTES", "assign:MAIN_BYTES", "assign:PAYLOAD_SHA256",
  "assign:PAYLOAD_BYTES", "assign:INDEX_SHA256", "assign:GENERATED_SHA256",
  "assign:HISTORICAL_BYTES", "assign:DUMP_SHA256", "assign:DUMP_BYTES",
  "assign:INDEX_INPUT_SHA256", "assign:ALIASES", "assign:EXPORTS",
  "assign:CONTROL_ROOT", "assign:LOOKUP_ROOT", "assign:EMPTY_CONFIG",
  "assign:EARLY_PATH", "assign:MAIN_PATH", "assign:MAX_INDEX_BYTES",
  "assign:MODULE_MODEL_SHA256", "assign:STRUCTURAL_BINDINGS",
  "assign:STRUCTURAL_RECORD_ROOT", "assign:STRUCTURAL_ARTIFACTS",
  "assign:REAL_OPERATIONAL_ARTIFACTS", "assign:STDOUT_BYTES", "assign:STDERR_BYTES",
  "assign:REPORT_BYTES", "assign:SEMANTIC_RECORDS", "assign:SEMANTIC_FIXTURE_PATHS",
  "assign:SEMANTIC_OPERATIONAL_PATHS", "assign:SEMANTIC_FIXTURE_PENDING",
  "assign:SEMANTIC_FIXTURE_RESULT", "assign:SEMANTIC_FIXTURE_WORK_MEMBERS",
  "assign:ARCHIVE_OBSERVATIONS", "assign:SEMANTIC_REPORT_KEYS",
  "assign:SEMANTIC_FILE_KEYS", "assign:SEMANTIC_DIRECTORY_KEYS",
  "assign:SEMANTIC_TREE_FILE_KEYS", "assign:RENAME_NOREPLACE", "assign:_AT_FDCWD",
  "class:ESelection", "class:Regeneration", "class:StructuralPolicy",
  "class:StructuralAcceptance", "class:RawControlFiles", "class:MappedControlOutputs",
  "class:SemanticFixtureEvaluation", "class:SemanticFixtureAcceptance",
  "function:_sha256", "function:_validated_names", "function:select_e",
  "function:validate_regeneration", "function:_probe", "function:command_plan",
  "function:_structural_identity", "function:_structural_read",
  "function:_structural_json", "function:_structural_record",
  "function:_structural_commands", "function:structural_policy",
  "function:_collect_fixed_raw_files", "function:_map_raw_control_outputs",
  "function:_read_fixed_semantic_fixture_outputs",
  "function:_read_fixed_operational_outputs", "function:_semantic_json",
  "function:_semantic_json_bytes", "function:_semantic_module_names",
  "function:_semantic_generated_relative", "function:_semantic_control_before",
  "function:_semantic_dependencies", "function:_semantic_expected_module",
  "function:_semantic_lookup_target", "function:_semantic_file_observation",
  "function:_semantic_stable_file", "function:_semantic_stable_tree",
  "function:_semantic_tree_identity_records", "function:_semantic_expected_provenance",
  "function:_semantic_provenance", "function:_semantic_command_plan",
  "function:_semantic_command_observation", "function:_semantic_identity_records",
  "function:_semantic_bound_observation", "function:_semantic_archive_records",
  "function:_semantic_aggregate", "function:_validate_file_metadata",
  "function:_validate_file_content", "function:_validate_command_shape",
  "function:_validate_archive_observation", "function:_validate_payload_observation",
  "function:_validate_tree_observation", "function:_validate_index_observation",
  "function:_validate_module_observation", "function:_validate_alias_observation",
  "function:_validate_symbol_observation", "function:_validate_command_observation",
  "function:_validate_identity_observation", "function:_validate_provenance_observation",
  "function:_validate_archive_family", "function:_validate_payload_family",
  "function:_validate_tree_family", "function:_validate_index_family",
  "function:_validate_module_family", "function:_validate_alias_family",
  "function:_validate_symbol_family", "function:_validate_command_family",
  "function:_validate_identity_family", "function:_validate_provenance_family",
  "function:_evaluate_control_semantics", "function:_rename_noreplace_errcheck",
  "assign:_SEMANTIC_LIBC", "assign:_SEMANTIC_LIBC.renameat2.argtypes",
  "assign:_SEMANTIC_LIBC.renameat2.restype", "assign:_SEMANTIC_LIBC.renameat2.errcheck",
  "function:_rename_noreplace", "function:_semantic_fixture_work_membership",
  "function:_semantic_fixture_result_bytes", "function:publish_semantic_fixture_result",
  "class:ExecutionPolicy", "class:OperationalPolicy", "class:OperationalAcceptance",
  "class:OperationalInputSnapshot", "class:OperationalContext",
  "class:OperationalEvaluation", "assign:EXECUTION_COMMAND",
  "assign:EXECUTION_ENVIRONMENT", "assign:EXECUTION_TASK_BINDINGS",
  "assign:EXECUTION_UID", "assign:EXECUTION_GID", "assign:EXECUTION_CWD",
  "assign:EXECUTION_UMASK", "assign:EXECUTION_RUNTIME_MOUNTS",
  "assign:EXECUTION_FIXED_SANDBOX_MOUNTS", "assign:EXECUTION_TASK_INPUTS",
  "assign:EXECUTION_READ_ONLY_MOUNTS", "assign:EXECUTION_PLANNED_CHILDREN",
  "assign:EXECUTION_CONTROL_SECONDS", "assign:EXECUTION_CHILD_SECONDS",
  "assign:EXECUTION_WORKLOAD_SECONDS", "assign:EXECUTION_OUTER_SECONDS",
  "assign:EXECUTION_MODE", "assign:OPERATIONAL_RECORD_ROOT",
  "assign:OPERATIONAL_ARTIFACTS", "assign:OPERATIONAL_RESULT_PENDING",
  "assign:OPERATIONAL_PROOF_PATH", "assign:OPERATIONAL_PROOF_SHA256",
  "assign:OPERATIONAL_RECIPE_LIMIT", "assign:OPERATIONAL_HEADER_LIMIT",
  "assign:OPERATIONAL_EVIDENCE_LIMIT", "assign:OPERATIONAL_INDEX_INPUTS",
  "assign:OPERATIONAL_INPUT_MEMBERS", "assign:OPERATIONAL_INITIAL_WORK_MEMBERS",
  "assign:OPERATIONAL_REPORT_KEYS", "assign:OPERATIONAL_STDOUT_LIMITS",
  "assign:OPERATIONAL_STDERR_LIMIT", "assign:OPERATIONAL_REPORT_LIMIT",
  "assign:OPERATIONAL_EMPTY_CONFIG_LIMIT", "assign:OPERATIONAL_EARLY_STREAM_LIMIT",
  "assign:OPERATIONAL_MAIN_STREAM_LIMIT", "assign:OPERATIONAL_RECORD_FILES",
  "assign:OPERATIONAL_CONTROL_TREE_FILES", "assign:OPERATIONAL_LOOKUP_TREE_FILES",
  "assign:OPERATIONAL_TREE_DIRECTORIES", "assign:OPERATIONAL_TREE_MAX_DEPTH",
  "assign:OPERATIONAL_TREE_FILE_LIMIT", "assign:OPERATIONAL_TREE_AGGREGATE_LIMIT",
  "function:operational_execution_policy", "function:_read_bounded_operational_file",
  "function:_operational_record_path", "function:_validate_operational_record_root",
  "function:_bounded_operational_tree", "function:_collect_operational_outputs",
  "function:_read_exact_operational_input", "function:_capture_operational_input_directory",
  "function:_capture_operational_inputs", "function:_operational_input_bytes",
  "function:_operational_builtins", "function:_operational_policy_from_inputs",
  "function:_operational_work_membership", "function:_capture_operational_materialized_file",
  "function:_materialize_operational_context", "function:_run_operational_commands",
  "function:_operational_json", "function:_operational_tree_file_record",
  "function:_validate_operational_records", "function:_read_operational_generated_indexes",
  "function:_validate_operational_roots", "function:_operational_lookup_target",
  "function:_validate_operational_semantics", "function:_operational_input_records",
  "function:_operational_full_tree_identities", "function:_operational_header_bytes",
  "function:_operational_evidence_bytes", "function:_operational_result_bytes",
  "function:_finalize_executed_operational_result", "function:_run_operational_control",
  "function:operational_policy", "function:finalize_operational_result",
  "function:finalize_structural_result", "function:main", "guard:main",
)


OPERATIONAL_FIXED_NODES = (
  ("import:math", "f329650e2c61a07a1bab85b32296a6d93760e313e108904819fa27d09cf3954d"),
  ("importfrom:e_control", "5d19599a4594c6de548e06861a6f6416e073d08d6d5792b3cb28ca5e34900eec"),
  ("assign:REAL_OPERATIONAL_ARTIFACTS", "dfcaa10dfa1a823031928b92e66f6f8b0fe2fbc5b900a278c82ae236facd2ba1"),
)
OPERATIONAL_BLOCK_MANIFEST = (
  ("class:ExecutionPolicy", "ddebb0c0b6db064f7497c60632656b42667b12ce453bdbf1c2ba6ffa5a6ee680"),
  ("class:OperationalPolicy", "2502d2178686ca55f42fff73e2d6e92f4d03359b40789fbf4dac9af60b3325ed"),
  ("class:OperationalAcceptance", "5513d08d8681a37b65974f51335a7c3469385cdc1a899a17bca346ce92d0a64a"),
  ("class:OperationalInputSnapshot", "33c5c84af40a88a822a8a6fd135ae31ea381c519e3e19a39656a439f6b2b35d9"),
  ("class:OperationalContext", "bd516555df29980ce8c498326336c05b274302ded4596c683c029a3aac294c80"),
  ("class:OperationalEvaluation", "3bbec743b4484105784d34f84e8b40f9ae6d7b3c9a8ada6fbb288ab5576d6937"),
  ("assign:EXECUTION_COMMAND", "1a5018aa31ebdb8358a3a8badaec4f4e6ed452b45949e5a3679ef7eb88e3d995"),
  ("assign:EXECUTION_ENVIRONMENT", "f40f4d8201d5bdec2c89ccf45d6f9e70b469788397d9b02b2d14e3693ee3dc9c"),
  ("assign:EXECUTION_TASK_BINDINGS", "344fd4ecf2be39590dbe4bd21d462277c45690ff2ed6a1c8ec11e81a8aa92171"),
  ("assign:EXECUTION_UID", "eb433e1f346c7efc0fd3a8019ae63edc79848bfa2c2807f8fc1a38c53ffac483"),
  ("assign:EXECUTION_GID", "fdc6f4cddf9342019df7dd786f67d53aaf6fa0154e25b39280318062c44b9ee1"),
  ("assign:EXECUTION_CWD", "d6befb9b236cf3cd8ee1fd427047d9b313403b711179fc754dbe5c58b349792d"),
  ("assign:EXECUTION_UMASK", "52d4ee5b6ab02fb38a3cb0be584dabe9170d496621a49713062ee7f52436eb7c"),
  ("assign:EXECUTION_RUNTIME_MOUNTS", "08c3874043b833c4c1f6e302514c1d75a3887567873243a27a5c37fddea7aa0f"),
  ("assign:EXECUTION_FIXED_SANDBOX_MOUNTS", "3d88bd1940e49e05849247b7805a97645f4febc6ee50c1c0542d91103227127f"),
  ("assign:EXECUTION_TASK_INPUTS", "4facfcd3bdc89356cd2a3df43fb15a9a46433a60d0eb376b68aa7b0590b2aacb"),
  ("assign:EXECUTION_READ_ONLY_MOUNTS", "2688f9f1dfcaaa3e03a5fefe40a483399bd2f840f83bf456cc1c76d8a3bdb810"),
  ("assign:EXECUTION_PLANNED_CHILDREN", "a79d98a5c0205c746ad87ccf61070ba6c4bef5624e2a7467842034a381c98ac9"),
  ("assign:EXECUTION_CONTROL_SECONDS", "df5dceca287915d53bd5269152f7d34f0576d0461c788da07687571e71d23930"),
  ("assign:EXECUTION_CHILD_SECONDS", "7db7a52dcc3783134df73092d3dcb0c590b06909dae123b3a3fa928035c27f8f"),
  ("assign:EXECUTION_WORKLOAD_SECONDS", "16bee1ac407b19032da80e7ec96a4060044ec7b1eaf3ab7a31ecec0ea0c47122"),
  ("assign:EXECUTION_OUTER_SECONDS", "87f462b46ea095cf7241cb45e13260d088df3f316a32add890330e30feae95bc"),
  ("assign:EXECUTION_MODE", "b9903d654e25291fbe91c79b526591889f44c6901a8c1b340adc8924b1da1f62"),
  ("assign:OPERATIONAL_RECORD_ROOT", "21dba0709d81ede44b06a8d2dc917c128ad99251b04033dec452f86902855ca1"),
  ("assign:OPERATIONAL_ARTIFACTS", "e9f855509362a454d0139da913c09f45f3d6b7cfdd31c5b707d9375e3e2394b3"),
  ("assign:OPERATIONAL_RESULT_PENDING", "d3848a37d9acebbbd6731e197a2acf0843738201a15de25b9e56a3d0e0554179"),
  ("assign:OPERATIONAL_PROOF_PATH", "0ff684cda75fc829abf339763d34ea60c5dd41b489e3dd981506a9bdcdd6de66"),
  ("assign:OPERATIONAL_PROOF_SHA256", "5dc7cbd8c6e93ce5e1eb42436a14f4df77d18cdd14e582c1c1da52c319a57294"),
  ("assign:OPERATIONAL_RECIPE_LIMIT", "03611864f360d6cb5eb64111045a288c7d93b447dddc07ecfec4c50c8ef7a5b5"),
  ("assign:OPERATIONAL_HEADER_LIMIT", "5fa0089cd85c3c7efa30a3a96ecc08d3d259b3f8216ee82433c8a7e859ed1588"),
  ("assign:OPERATIONAL_EVIDENCE_LIMIT", "9b75595769e52b01144d35f35eabde037b0c6d4199ded0aa3dd0b7d5b7fdcc53"),
  ("assign:OPERATIONAL_INDEX_INPUTS", "ae9b5a636c3ec030e37782968cfe81c6fcd0e52d85e735e73d25c52df20a8dff"),
  ("assign:OPERATIONAL_INPUT_MEMBERS", "8d93483e7f1eeef034d043b8e558ab2fd72729f9ad75ec5d92b286eae29afbf7"),
  ("assign:OPERATIONAL_INITIAL_WORK_MEMBERS", "e3e50812cd9c93b7e86d7929d144737274efce8d23d0ebd3e3395931f707b3cc"),
  ("assign:OPERATIONAL_REPORT_KEYS", "02ae986ee9e4fa3352c1f4bb9488a9ceca1743bb83d6f0d2804683fd1d62c9fd"),
  ("assign:OPERATIONAL_STDOUT_LIMITS", "dde0edeb9ba3dba2d4b7b63d7be5e7ad0bf4e849538062ba6bcdbdf97f0c6b19"),
  ("assign:OPERATIONAL_STDERR_LIMIT", "7ee739aada236807765f5442de26deb58c78a85d29b0b07f7afc8f195aab8ff0"),
  ("assign:OPERATIONAL_REPORT_LIMIT", "d7b20c432165ac161669568c98b2ce8133c9d52bc8d7aa8c09e8745dfd824ae9"),
  ("assign:OPERATIONAL_EMPTY_CONFIG_LIMIT", "1a65d071595c13672f22a91875b4159f8a3a8db9122bf1609920121be9ac68ba"),
  ("assign:OPERATIONAL_EARLY_STREAM_LIMIT", "5564cc75cf896ef2d6e6a7a48737b948d4f9666f8a6906c78bc97a21b4213842"),
  ("assign:OPERATIONAL_MAIN_STREAM_LIMIT", "81d4eae5e1f11faa14e62cf304e4f18ecd78563cdaa5e5057e34eaba17f3f857"),
  ("assign:OPERATIONAL_RECORD_FILES", "de872e1707a8acdbf95a8678f656828cf817a900a55b76c085570ee7b01210ce"),
  ("assign:OPERATIONAL_CONTROL_TREE_FILES", "86ffd32863eaca78aad9318d271e98675bbf8f7ceac8fafbf5f169f73341509c"),
  ("assign:OPERATIONAL_LOOKUP_TREE_FILES", "d3d3c23a112100d50550f969a64f34aef2cca8254c74817318d0c6f14b8ee635"),
  ("assign:OPERATIONAL_TREE_DIRECTORIES", "9430df4f22533bd84b3e1687816a9e9c8a8ab056e46152c5d64a90a304d479f1"),
  ("assign:OPERATIONAL_TREE_MAX_DEPTH", "73bfac371b2fa69988cf3b399f50a10eaf225e6e39b3a1966ddd2ae382619455"),
  ("assign:OPERATIONAL_TREE_FILE_LIMIT", "d7c9e4f2710aea60fcfebea986f1176a6ffd50982cf785bfd53fb4f21c0b2d82"),
  ("assign:OPERATIONAL_TREE_AGGREGATE_LIMIT", "fd988110656cdb0eb137f3139405f9f2ecab3a46d142aa650c3b40bb972f8ba4"),
  ("function:operational_execution_policy", "eb52d9c172e11c26d3234c113b1ab2f457bcdaaeead34d8bd07d6c6c0667ab96"),
  ("function:_read_bounded_operational_file", "c6de89fb4352285519fd126957655b3971f2f5330d8388d039a30c992f1fd376"),
  ("function:_operational_record_path", "9d8b90d82d6dd3e31747293a10c2289ce3089c44a598b6d12ec41922260557a7"),
  ("function:_validate_operational_record_root", "cad843147a3a32b6cbb5aac72b2d36ec30f20c219f62896b0e888b10e9ec50a9"),
  ("function:_bounded_operational_tree", "341f88371870002e0579fb31aae2dff7faf1fd524c78733acc7fffcde8164545"),
  ("function:_collect_operational_outputs", "ada730fc7dbf1e1ee105afb55451952c3e4e1fb13bef27b4220706b61b3e0327"),
  ("function:_read_exact_operational_input", "4bb672105c76ee25ed996d8db7d87b683b5aaa880bbde79bfa43e8f871a3c405"),
  ("function:_capture_operational_input_directory", "a511635e4c3661ac015354c635384ac6435d94c079ffc9790af9391886719a1c"),
  ("function:_capture_operational_inputs", "b3e844757589ddc654135a28b45d1efecfc64043abe700ab93f02130385f75c2"),
  ("function:_operational_input_bytes", "4d85a91a87268e76a32645827b5c48137fd128c4cb0b7a04d0ab658fca1fddf7"),
  ("function:_operational_builtins", "bec99f1ffd1563333377ea728f459ec4b2e9d72b898592a52b3de9029dd10672"),
  ("function:_operational_policy_from_inputs", "00aef061150731ba902767fa49300d12b7b68c5c673df762f47e33f0f47a8c4b"),
  ("function:_operational_work_membership", "5094c50d5c88b9ed388ad6566251e149295bc25d89d4dba9de0d97e9c762a0fb"),
  ("function:_capture_operational_materialized_file", "5d3007ef5f99696a588582d7c7e693c593210e920e613c9b4512c6d926219a20"),
  ("function:_materialize_operational_context", "e243c8c8156ddab2055ce2b899cf2dbd97fa04999362fd4d36c0fd413b7adb32"),
  ("function:_run_operational_commands", "8dbb5a974157cb07feea15209709400f1900475d6e7e64e19f2619aa6b00bd6f"),
  ("function:_operational_json", "ba67d651f83b4fe5364f603c8ead45a8c16c4c0f1490048fa4552d5e0ccdac2a"),
  ("function:_operational_tree_file_record", "b99cd7c30e39387880e5c7e391ea39ee0f45d9c5eb031f8403b82a052fad2477"),
  ("function:_validate_operational_records", "e1bbc711e6708c14c1b3b4e3733feaacd25eb784e113dbc9cd1ed03f90338e13"),
  ("function:_read_operational_generated_indexes", "29426c53e221a0a6c630ff6a248825d7622f9cf5b04ecc236373718b2661487f"),
  ("function:_validate_operational_roots", "3832c2b29e0db09effd2b88863838efdef9651c07097da8a25da4c45ae4fa685"),
  ("function:_operational_lookup_target", "da248544acff8518e4b3c5731e08ff20451340ca3fe7ddd770847d48c41d0274"),
  ("function:_validate_operational_semantics", "1b40b3ae7ed2d052e48abc55f01e5c6f4603e9aa828e020133b455d30cbc5217"),
  ("function:_operational_input_records", "490adfe26f48e7db9d74a4672a4719092510196e138a28253817757f8df152f2"),
  ("function:_operational_full_tree_identities", "a0e8926202aab88f9d3e26ab4a2d336a18fe7e8ed725eb7a0003b9fad7f70648"),
  ("function:_operational_header_bytes", "8f8834ad368b29632c731af083a96ad13f97ddebc59f8274947d69bf0d9e77eb"),
  ("function:_operational_evidence_bytes", "a0b56be3e4acc74da8ff49717b1eef9919ddda944785c51f3edfbf3a2055f66d"),
  ("function:_operational_result_bytes", "10e3bc0782fa379e524e8e2b7898aa320ac9a3aebbf9ec2639518e2c41a9323c"),
  ("function:_finalize_executed_operational_result", "9d5cce2401180221338445d2b71d1ff160fc26729aa763a4970f5a0732a4807a"),
  ("function:_run_operational_control", "cd58764fbcd7281febc5d3934513bfbc775f1bf1176adfcd946863907ff2ddf8"),
  ("function:operational_policy", "98bca2b5ac333292d85fb3e9ee5e882a808e5e9d42b08934dcb8593b3e286c1c"),
  ("function:finalize_operational_result", "7a672e89b4e6f0ae3c02efe76c9863b1296e9352938c82c4b4603ccd9fe0e2dc"),
  ("function:finalize_structural_result", "b9134fb21410042da05a0f1193980a4d7871cecd56ab80e75de8328baf7f57d0"),
  ("function:main", "b0a5243a116d754e33f65d55fd2a4b9d6fcdde0c9916c301795c9b860ddcfe94"),
  ("guard:main", "3340fd16ba41ba1ddf3989cd136a498b72a97f7796e0f7fad6e815585dbc1c52"),
)


def require_operational_recipe_contract(tree: ast.Module) -> None:
  manifest = node_manifest(tree.body)
  labels = tuple(label for label, _ in manifest)
  require(
    len(labels) == len(OPERATIONAL_FULL_TOP_LEVEL_LABELS) == 230
    and len(set(labels)) == len(labels)
    and labels == OPERATIONAL_FULL_TOP_LEVEL_LABELS,
    "fixed full top-level membership, count, or order differs",
  )
  by_label: dict[str, list[tuple[ast.stmt, str]]] = {}
  for node, (label, digest) in zip(tree.body, manifest, strict=True):
    by_label.setdefault(label, []).append((node, digest))
  for label, digest in OPERATIONAL_FIXED_NODES:
    require(by_label.get(label) is not None and len(by_label[label]) == 1
            and by_label[label][0][1] == digest,
            f"fixed operational import or artifact node differs: {label}")
  block_labels = tuple(label for label, _ in OPERATIONAL_BLOCK_MANIFEST)
  start = next((index for index, item in enumerate(manifest)
                if item[0] == "class:ExecutionPolicy"), -1)
  require(start >= 0 and manifest[start:] == OPERATIONAL_BLOCK_MANIFEST,
          "fixed operational block AST or ordering differs")
  require(tuple(label for label, _ in manifest[start:]) == block_labels,
          "fixed operational block labels differ")

  baseline_exceptions = {
    "expr:docstring", "assign:REAL_OPERATIONAL_ARTIFACTS",
    "function:operational_policy", "function:finalize_operational_result",
    "function:main",
  }
  for label, digest in BASELINE_TOP_LEVEL_MANIFEST:
    if label not in baseline_exceptions:
      require(by_label.get(label) is not None and len(by_label[label]) == 1
              and by_label[label][0][1] == digest,
              f"accepted baseline node differs: {label}")
  for label, expected in FUTURE_REFERENCE_DUMPS.items():
    require(by_label.get(label) is not None and len(by_label[label]) == 1
            and normalized_node_dump(by_label[label][0][0]) == expected,
            f"accepted fixed execution boundary differs: {label}")

  functions = {
    node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
  }
  operational_names = {
    label.removeprefix("function:") for label in block_labels
    if label.startswith("function:") and label not in {
      "function:finalize_structural_result", "function:main",
    }
  }
  graph: dict[str, frozenset[str]] = {}
  for name in operational_names:
    graph[name] = frozenset(
      call.func.id for call in ast.walk(functions[name])
      if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
      and call.func.id in operational_names
    )
  expected_graph = {
    "_validate_operational_record_root": frozenset((
      "_operational_record_path", "_read_bounded_operational_file",
    )),
    "_bounded_operational_tree": frozenset(("_read_bounded_operational_file",)),
    "_collect_operational_outputs": frozenset((
      "_validate_operational_record_root", "_bounded_operational_tree",
      "_read_bounded_operational_file", "_operational_record_path",
    )),
    "_capture_operational_inputs": frozenset((
      "_read_exact_operational_input", "_capture_operational_input_directory",
    )),
    "_operational_policy_from_inputs": frozenset((
      "_operational_builtins", "_operational_input_bytes",
      "operational_execution_policy",
    )),
    "_capture_operational_materialized_file": frozenset((
      "_read_bounded_operational_file",
    )),
    "_materialize_operational_context": frozenset((
      "_capture_operational_inputs", "_operational_policy_from_inputs",
      "_operational_input_bytes", "_capture_operational_materialized_file",
      "_operational_work_membership",
    )),
    "_run_operational_commands": frozenset(("_collect_operational_outputs",)),
    "_validate_operational_records": frozenset((
      "_operational_json", "_operational_tree_file_record",
    )),
    "_read_operational_generated_indexes": frozenset((
      "_read_bounded_operational_file",
    )),
    "_validate_operational_semantics": frozenset((
      "_validate_operational_roots", "_read_operational_generated_indexes",
      "_operational_lookup_target",
    )),
    "_operational_evidence_bytes": frozenset((
      "_operational_input_bytes", "_operational_input_records",
    )),
    "_finalize_executed_operational_result": frozenset((
      "_operational_header_bytes", "_operational_evidence_bytes",
      "_capture_operational_materialized_file", "_collect_operational_outputs",
      "_operational_result_bytes", "_operational_full_tree_identities",
      "_capture_operational_inputs", "_operational_work_membership",
    )),
    "_run_operational_control": frozenset((
      "_materialize_operational_context", "_run_operational_commands",
      "_validate_operational_records", "_validate_operational_semantics",
      "_finalize_executed_operational_result",
    )),
    "operational_policy": frozenset((
      "_capture_operational_inputs", "_operational_policy_from_inputs",
    )),
  }
  require(all(graph[name] == expected_graph.get(name, frozenset())
              for name in graph), "fixed operational internal call graph differs")
  reachable = {"_run_operational_control"}
  pending = ["_run_operational_control"]
  while pending:
    for name in graph[pending.pop()] - reachable:
      reachable.add(name)
      pending.append(name)
  require(operational_names - {"operational_policy", "finalize_operational_result"}
          <= reachable, "fixed operational call graph is not closed from main")

  constructors = [
    (name, call) for name in operational_names for call in ast.walk(functions[name])
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    and call.func.id == "Commands"
  ]
  runner_calls = [
    (name, call) for name in operational_names for call in ast.walk(functions[name])
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    and isinstance(call.func.value, ast.Name) and call.func.value.id == "runner"
    and call.func.attr == "run"
  ]
  require(len(constructors) == 1 and constructors[0][0] == "_run_operational_commands"
          and len(runner_calls) == 2
          and all(name == "_run_operational_commands" for name, _ in runner_calls),
          "Commands is not the sole fixed workload launch site")
  forbidden = {"fork", "forkpty", "posix_spawn", "posix_spawnp", "system", "popen"}
  require(not any(
    isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    and isinstance(call.func.value, ast.Name) and call.func.value.id == "os"
    and call.func.attr in forbidden
    for name in operational_names for call in ast.walk(functions[name])
  ), "operational path reaches an alternate process API")

  sequence = functions["_run_operational_control"].body
  require(
    len(sequence) == 5
    and [statement.targets[0].id for statement in sequence[:4]
         if isinstance(statement, ast.Assign)]
    == ["context", "raw_files", "records", "evaluation"]
    and isinstance(sequence[-1], ast.Return)
    and isinstance(sequence[-1].value, ast.Call)
    and isinstance(sequence[-1].value.func, ast.Name)
    and sequence[-1].value.func.id == "_finalize_executed_operational_result",
    "fixed execute, collect, validate, finalize order differs",
  )
  finalizer = functions["_finalize_executed_operational_result"]
  finalizer_calls = [
    call for call in ast.walk(finalizer) if isinstance(call, ast.Call)
  ]
  write_targets = [
    call.args[0].id for call in finalizer_calls
    if isinstance(call.func, ast.Name) and call.func.id == "write_new"
    and len(call.args) == 2 and isinstance(call.args[0], ast.Name)
  ]
  named_calls = [
    call.func.id for call in finalizer_calls if isinstance(call.func, ast.Name)
  ]
  require(
    write_targets == ["header_path", "evidence_path", "pending_path"]
    and named_calls.count("_rename_noreplace") == 1
    and named_calls.count("_capture_operational_inputs") == 1
    and named_calls.count("_collect_operational_outputs") == 1
    and named_calls.count("_operational_full_tree_identities") == 6
    and isinstance(finalizer.body[-4], ast.Expr)
    and isinstance(finalizer.body[-4].value, ast.Call)
    and isinstance(finalizer.body[-4].value.func, ast.Name)
    and finalizer.body[-4].value.func.id == "write_new"
    and isinstance(finalizer.body[-4].value.args[0], ast.Name)
    and finalizer.body[-4].value.args[0].id == "pending_path"
    and isinstance(finalizer.body[-3], ast.Expr)
    and isinstance(finalizer.body[-3].value, ast.Call)
    and isinstance(finalizer.body[-3].value.func, ast.Name)
    and finalizer.body[-3].value.func.id == "_require"
    and isinstance(finalizer.body[-2], ast.Expr)
    and isinstance(finalizer.body[-2].value, ast.Call)
    and isinstance(finalizer.body[-2].value.func, ast.Name)
    and finalizer.body[-2].value.func.id == "_rename_noreplace"
    and all(isinstance(argument, ast.Name) for argument in finalizer.body[-2].value.args)
    and [argument.id for argument in finalizer.body[-2].value.args]
    == ["pending_path", "result_path"]
    and isinstance(finalizer.body[-1], ast.Return)
    and isinstance(finalizer.body[-1].value, ast.Name)
    and finalizer.body[-1].value.id == "acceptance",
    "pending verification or result-last no-replace publication differs",
  )


def pre_vet_subject(raw: bytes) -> tuple[ast.Module, bool]:
  tree = ast.parse(raw, filename=str(SUBJECT), mode="exec")
  actual = node_manifest(tree.body)
  if actual == BASELINE_TOP_LEVEL_MANIFEST:
    return tree, False
  if any(label == "class:OperationalPolicy" for label, _ in actual):
    require_operational_recipe_contract(tree)
    return tree, True
  future_subject = actual == FUTURE_TOP_LEVEL_MANIFEST
  require(future_subject,
          "subject top-level manifest or fixed future ordering differs")
  actual_nodes = {top_level_label(node): normalized_node_dump(node) for node in tree.body}
  require(
    set(FUTURE_REFERENCE_DUMPS) <= set(actual_nodes)
    and all(actual_nodes[label] == expected
            for label, expected in FUTURE_REFERENCE_DUMPS.items()),
    "future execution boundary differs from the exact AST reference templates",
  )
  require(
    sum(label == "guard:main" for label, _ in actual) == 1
    and actual[-1] == BASELINE_TOP_LEVEL_MANIFEST[-1],
    "exact guarded main call is not sole and last",
  )
  return tree, future_subject


def operational_contract_mutation_probe() -> None:
  source = INPUT_BYTES[SUBJECT].decode("utf-8")
  mutations = (
    (
      "@dataclass(frozen=True)\nclass ExecutionPolicy:",
      "_semantic_fixture_work_membership()\n\n"
      "@dataclass(frozen=True)\nclass ExecutionPolicy:",
    ),
    (
      "@dataclass(frozen=True)\nclass ExecutionPolicy:",
      "Commands = None\n\n@dataclass(frozen=True)\nclass ExecutionPolicy:",
    ),
    ("OPERATIONAL_STDERR_LIMIT = 1", "OPERATIONAL_STDERR_LIMIT = 2"),
    ("runner = Commands(", "runner = CommandsDecoy("),
    (
      "records = _validate_operational_records(context, raw_files)\n"
      "  evaluation = _validate_operational_semantics(context, raw_files, records)",
      "evaluation = _validate_operational_semantics(context, raw_files, records)\n"
      "  records = _validate_operational_records(context, raw_files)",
    ),
    ("write_new(pending_path, result_raw)", "write_new(result_path, result_raw)"),
    (
      "_capture_operational_materialized_file(pending_path, result_raw)",
      "_capture_operational_materialized_file(header_path, result_raw)",
    ),
    (
      "_capture_operational_inputs() == context.inputs",
      "context.inputs == context.inputs",
    ),
    (
      "_rename_noreplace(pending_path, result_path)\n  return acceptance",
      "_rename_noreplace(pending_path, result_path)\n"
      "  _sha256(result_raw)\n  return acceptance",
    ),
  )
  for old, new in mutations:
    require(source.count(old) == 1, "operational mutation source is not unique")
    changed = source.replace(old, new, 1)
    try:
      require_operational_recipe_contract(
        ast.parse(changed, filename=str(SUBJECT), mode="exec"),
      )
    except RuntimeError:
      continue
    raise RuntimeError("operational contract accepted a cap, launch, order, or publication mutation")


def bootstrap() -> tuple[
  ModuleType, ModuleType, dict[Path, bytes], dict[Path, tuple[int, ...]],
  dict[str, bytes], tuple[int, ...], dict[str, tuple[int, ...]], ast.Module,
]:
  require(sys.argv[1:] == list(SELECTED_TESTS), "unapproved selected tests")
  require(
    sys.version_info[:2] == (3, 14)
    and sys.flags.isolated == 1
    and sys.flags.no_site == 1
    and sys.dont_write_bytecode,
    "isolated Python 3.14 required",
  )
  require(
    os.getuid() == os.geteuid() == os.getgid() == os.getegid() == 1001
    and Path.cwd() == Path("/work"),
    "unexpected test identity or directory",
  )
  require(Path(__file__) == TEST, "unexpected runner path")
  require(
    tuple(sys.path) == ORIGINAL_SYS_PATH
    and not any(Path(path).is_relative_to("/inputs") for path in sys.path),
    "isolated Python path differs before dependency loading",
  )
  require(
    not any(Path(path).exists() for path in (
      "/proc", "/sys", "/run", "/home", "/root", "/boot", "/etc",
    )),
    "host tree visible",
  )
  require(
    not any(name in sys.modules for name in (
      "cpio_image", "verify_control", "prepare_image", "t1_image_contract",
      "e_control", "e_recipe",
    )),
    "dependency already imported",
  )
  validate_binding_tree()
  data = {path: read_pinned(path) for path in PINS}
  source_tree, future_subject = pre_vet_subject(data[SUBJECT][0])
  indexes, index_state, index_file_states = read_index_directory()
  try:
    if future_subject:
      subject = load_source("e_recipe", SUBJECT, data[SUBJECT][0])
      require(
        tuple(
          getattr(sys.modules.get(name), "__file__", None)
          for name, _, _ in SOURCE_INPUTS
        ) == tuple(str(path) for _, path, _ in SOURCE_INPUTS),
        "fixed self-bootstrap source files differ",
      )
      commands = sys.modules["e_control"]
      require(isinstance(commands, ModuleType), "fixed command module type differs")
    else:
      assembly = load_source("prepare_image", ASSEMBLY, data[ASSEMBLY][0])
      require(
        assembly.__file__ == str(ASSEMBLY)
        and sys.modules["verify_control"].__file__ == str(CONTROL)
        and sys.modules["cpio_image"].__file__ == str(HELPER),
        "accepted assembly dependency loader differs",
      )
      load_source("t1_image_contract", CONTRACT, data[CONTRACT][0])
      commands = load_source("e_control", COMMANDS, data[COMMANDS][0])
      subject = load_source("e_recipe", SUBJECT, data[SUBJECT][0])
  finally:
    sys.path[:] = ORIGINAL_SYS_PATH
  require(
    tuple(sys.path) == ORIGINAL_SYS_PATH
    and not any(Path(path).is_relative_to("/inputs") for path in sys.path),
    "dependency loader did not restore the isolated Python path",
  )
  return (
    subject, commands, {path: pair[0] for path, pair in data.items()},
    {path: pair[1] for path, pair in data.items()}, indexes, index_state,
    index_file_states, source_tree,
  )


try:
  (
    subject, commands, INPUT_BYTES, INPUT_STATES, INDEX_BYTES, INDEX_STATE,
    INDEX_FILE_STATES, SOURCE_TREE,
  ) = bootstrap()
except (OSError, RuntimeError, ValueError, SyntaxError, ImportError, TypeError) as error:
  print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
  raise SystemExit(2) from None


def no_operational_outputs() -> None:
  require(
    not any(path.exists() or path.is_symlink() for path in FORBIDDEN_OUTPUTS),
    "operational output exists during zero-child RED",
  )
  require(not list(Path("/work").glob("e-control-children-*")), "workload child output exists")


def closed_operational_apis(module: ModuleType) -> None:
  execution = runtime_function(module, "operational_execution_policy")()
  require(
    len(execution.task_bindings) == 8
    and execution.read_only_mounts == 593
    and execution.planned_children == 424,
    "fixed operational execution policy differs",
  )
  try:
    runtime_function(module, "finalize_operational_result")()
  except module.RecipeError as error:
    require(str(error) == "E_CONTROL_DIRECT_FINALIZE_UNAVAILABLE",
            "direct operational finalizer refusal differs")
  else:
    raise RuntimeError("direct operational finalizer is not closed")
  require(
    "_run_operational_control" in runtime_function(module, "main").__code__.co_names,
    "main does not use the fixed private operational sequence",
  )


def probe_command(root: str, target: str) -> tuple[str, ...]:
  return (
    "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", root,
    "-S", KERNEL, "-C", "/work/empty-modprobe.conf", target,
  )


def expected_plan(names: dict[str, str]) -> tuple[tuple[str, ...], ...]:
  plan: list[tuple[str, ...]] = []
  for path in ("/work/e-early.cpio", "/work/e-main.cpio"):
    plan.extend((
      ("/usr/bin/cpio", "--list", "--quiet", "--file", path),
      ("/usr/bin/bsdtar", "--list", "--file", path),
    ))
  plan.append(("/usr/bin/gzip", "-n"))
  for path in PAYLOADS:
    plan.append((
      "/usr/bin/bsdtar", "--extract", "--to-stdout", "--file",
      "/work/e-main.cpio", path,
    ))
  plan.append(("/usr/bin/depmod", "-b", "/work/control-root", KERNEL))
  plan.extend((
    probe_command("/work/control-root", "--show-config"),
    probe_command("/work/lookup-root", "--show-config"),
  ))
  for name in sorted(names):
    plan.append((
      "/usr/bin/modinfo", "-b", "/work/lookup-root", "-k", KERNEL,
      "-F", "filename", name,
    ))
    plan.append(probe_command("/work/lookup-root", name))
  plan.extend(probe_command("/work/lookup-root", alias) for alias in ALIASES)
  plan.extend(
    probe_command("/work/lookup-root", "symbol:" + symbol) for symbol in EXPORTS
  )
  return tuple(plan)


def require_unconditional_operational_holds() -> None:
  finalizer = function_node("finalize_operational_result")
  require(
    len(finalizer.body) == 2 and isinstance(finalizer.body[0], ast.Expr)
    and isinstance(finalizer.body[0].value, ast.Constant)
    and isinstance(finalizer.body[0].value.value, str)
    and isinstance(finalizer.body[1], ast.Raise)
    and finalizer.body[1].cause is None
    and isinstance(finalizer.body[1].exc, ast.Call)
    and isinstance(finalizer.body[1].exc.func, ast.Name)
    and finalizer.body[1].exc.func.id == "RecipeError"
    and len(finalizer.body[1].exc.args) == 1
    and isinstance(finalizer.body[1].exc.args[0], ast.Constant)
    and finalizer.body[1].exc.args[0].value == "E_CONTROL_DIRECT_FINALIZE_UNAVAILABLE"
    and not finalizer.body[1].exc.keywords,
    "direct operational finalizer is not an unconditional refusal",
  )
  main_node = function_node("main")
  main_body = main_node.body[1:] if ast.get_docstring(main_node, clean=False) is not None \
    else main_node.body
  require(
    len(main_body) == 1 and isinstance(main_body[0], ast.Expr)
    and isinstance(main_body[0].value, ast.Call)
    and isinstance(main_body[0].value.func, ast.Name)
    and main_body[0].value.func.id == "_run_operational_control"
    and not main_body[0].value.args and not main_body[0].value.keywords,
    "main is not the exact fixed private operational entry",
  )


def pure_setup_checks() -> None:
  require(len(PRODUCTION_BINDINGS) == len(set(PRODUCTION_BINDINGS)) == 8,
          "production binding count differs")
  require(
    RUNTIME_MOUNTS + FIXED_SANDBOX_MOUNTS + PRODUCTION_TASK_INPUTS
    == PRODUCTION_READ_ONLY_MOUNTS == 593,
    "production mount prediction differs",
  )
  require(
    RUNTIME_MOUNTS + FIXED_SANDBOX_MOUNTS + TEST_TASK_INPUTS
    == TEST_READ_ONLY_MOUNTS == 594,
    "test mount prediction differs",
  )
  require(len(STDOUT_LIMITS) == PLANNED_CHILDREN, "stdout cap count differs")
  selection = subject.select_e(INPUT_BYTES[BASE])
  names = {module.name: str(module.relative) for module in selection.modules}
  plan = subject.command_plan(names)
  independent_plan = expected_plan(names)
  require(
    len(names) == 200
    and len(plan) == PLANNED_CHILDREN
    and plan == independent_plan
    and all(commands.approved_command(command) for command in plan)
    and not commands.approved_command(("/usr/bin/gzip",))
    and not any(command[0] == "/usr/bin/python3.14" for command in plan),
    "authenticated pure E command plan differs",
  )
  require_unconditional_operational_holds()
  closed_operational_apis(subject)
  no_operational_outputs()


def function_node(name: str) -> ast.FunctionDef:
  matches = [
    node for node in SOURCE_TREE.body
    if isinstance(node, ast.FunctionDef) and node.name == name
  ]
  require(len(matches) == 1, f"{name} definition count differs")
  return matches[0]


def runtime_function(module: ModuleType, name: str) -> Callable[..., object]:
  node = function_node(name)
  value = getattr(module, name, None)
  code = getattr(value, "__code__", None)
  require(
    callable(value) and code is not None
    and value.__name__ == name
    and code.co_filename == str(SUBJECT)
    and code.co_firstlineno == node.lineno,
    f"runtime {name} is not the authenticated function definition",
  )
  return value


def operational_publication_fault_shape_probe() -> None:
  finalizer = function_node("_finalize_executed_operational_result")
  require(not any(isinstance(node, ast.Try) for node in ast.walk(finalizer)),
          "operational publisher can catch or continue after a publication fault")
  pending_write, verification, publication, returned = finalizer.body[-4:]
  require(
    isinstance(pending_write, ast.Expr) and isinstance(pending_write.value, ast.Call)
    and isinstance(pending_write.value.func, ast.Name)
    and pending_write.value.func.id == "write_new"
    and isinstance(pending_write.value.args[0], ast.Name)
    and pending_write.value.args[0].id == "pending_path"
    and isinstance(verification, ast.Expr) and isinstance(verification.value, ast.Call)
    and isinstance(verification.value.func, ast.Name)
    and verification.value.func.id == "_require"
    and isinstance(publication, ast.Expr) and isinstance(publication.value, ast.Call)
    and isinstance(publication.value.func, ast.Name)
    and publication.value.func.id == "_rename_noreplace"
    and isinstance(returned, ast.Return),
    "operational publication fault boundary differs",
  )
  final_writes = [
    call for call in ast.walk(finalizer)
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    and call.func.id == "write_new" and call.args
    and isinstance(call.args[0], ast.Name) and call.args[0].id == "result_path"
  ]
  require(not final_writes,
          "a pending-write or verification fault could leave a final result")


def require_fixed_self_bootstrap() -> None:
  self_bootstrap = function_node("_bootstrap_fixed_sources")
  loader = function_node("_load_fixed_source")
  identity_helper = function_node("_fixed_source_identity")
  require(getattr(subject, "FIXED_SOURCE_BYTES", None) == 128 * 1024,
          "fixed source byte cap differs")
  require(
    runtime_function(subject, "_bootstrap_fixed_sources").__code__.co_firstlineno
    == self_bootstrap.lineno
    and runtime_function(subject, "_load_fixed_source").__code__.co_firstlineno
    == loader.lineno
    and runtime_function(subject, "_fixed_source_identity").__code__.co_firstlineno
    == identity_helper.lineno,
    "runtime fixed bootstrap helpers are not the vetted definitions",
  )
  top_bootstrap = [
    index for index, node in enumerate(SOURCE_TREE.body)
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    and isinstance(node.value.func, ast.Name)
    and node.value.func.id == self_bootstrap.name and not node.value.args
    and not node.value.keywords
  ]
  dependency_imports = [
    index for index, node in enumerate(SOURCE_TREE.body)
    if isinstance(node, ast.ImportFrom)
    and node.module in {name for name, _, _ in SOURCE_INPUTS}
  ]
  require(
    len(top_bootstrap) == 1 and dependency_imports
    and top_bootstrap[0] < min(dependency_imports),
    "self-bootstrap is not reachable before fixed dependency imports",
  )
  require(
    getattr(subject, "FIXED_SOURCE_INPUTS", None)
    == tuple((name, str(path), digest) for name, path, digest in SOURCE_INPUTS),
    "fixed source bootstrap pins differ",
  )


def direct_import_probe() -> None:
  names = tuple(name for name, _, _ in SOURCE_INPUTS)
  require(
    tuple(sys.path) == ORIGINAL_SYS_PATH
    and not any(Path(path).is_relative_to("/inputs") for path in sys.path),
    "direct probe did not start with the clean isolated Python path",
  )
  saved_path = tuple(sys.path)
  saved_modules = dict(sys.modules)
  for name in names:
    sys.modules.pop(name)
  try:
    sys.path[:] = ORIGINAL_SYS_PATH
    probe = ModuleType("e_recipe_direct_import_probe")
    probe.__file__ = str(SUBJECT)
    exec(compile(INPUT_BYTES[SUBJECT], str(SUBJECT), "exec"), probe.__dict__)
    require(
      tuple(sys.path) == ORIGINAL_SYS_PATH
      and not any(Path(path).is_relative_to("/inputs") for path in sys.path),
      "fixed self-bootstrap leaked an input path",
    )
    closed_operational_apis(probe)
  finally:
    sys.modules.clear()
    sys.modules.update(saved_modules)
    sys.path[:] = saved_path
  require(
    tuple(sys.path) == ORIGINAL_SYS_PATH
    and set(sys.modules) == set(saved_modules)
    and all(sys.modules[name] is module for name, module in saved_modules.items()),
    "direct probe did not restore the full import state",
  )


def partial_import_probe() -> None:
  names = tuple(name for name, _, _ in SOURCE_INPUTS)
  saved_path = tuple(sys.path)
  saved_modules = dict(sys.modules)
  invalid = INPUT_BYTES[SUBJECT].replace(
    SOURCE_INPUTS[3][2].encode("ascii"), b"0" * 64, 1,
  )
  require(invalid != INPUT_BYTES[SUBJECT], "partial-import probe did not alter one direct pin")
  for name in names:
    sys.modules.pop(name)
  expected_partial_modules = dict(sys.modules)
  refused = False
  subject_restored = False
  try:
    sys.path[:] = ORIGINAL_SYS_PATH
    probe = ModuleType("e_recipe_partial_import_probe")
    probe.__file__ = str(SUBJECT)
    try:
      exec(compile(invalid, str(SUBJECT), "exec"), probe.__dict__)
    except RuntimeError as error:
      refused = str(error) == "E_CONTROL_SOURCE_INVALID"
      subject_restored = (
        tuple(sys.path) == ORIGINAL_SYS_PATH
        and set(sys.modules) == set(expected_partial_modules)
        and all(sys.modules[name] is module
                for name, module in expected_partial_modules.items())
        and not any(Path(value).is_relative_to("/inputs") for value in sys.path)
      )
  finally:
    sys.modules.clear()
    sys.modules.update(saved_modules)
    sys.path[:] = saved_path
  require(
    refused and subject_restored
    and tuple(sys.path) == ORIGINAL_SYS_PATH
    and set(sys.modules) == set(saved_modules)
    and all(sys.modules[name] is module for name, module in saved_modules.items())
    and not any(Path(value).is_relative_to("/inputs") for value in sys.path),
    "partial-import probe did not refuse and restore the full import state",
  )


def wrong_digest_probe() -> None:
  loader = runtime_function(subject, "_load_fixed_source")
  for name, path, digest in SOURCE_INPUTS[2:]:
    saved_path = tuple(sys.path)
    saved_modules = dict(sys.modules)
    sys.modules.pop(name)
    try:
      flipped = ("1" if digest[0] == "0" else "0") + digest[1:]
      wrong_digests = ("0" * 64, flipped)
      require(
        len(set(wrong_digests)) == 2
        and all(candidate != digest for candidate in wrong_digests),
        "wrong-digest probes are not two distinct nonmatching values",
      )
      for wrong_digest in wrong_digests:
        try:
          loader(name, str(path), wrong_digest)
        except subject.RecipeError as error:
          require(str(error) == "E_CONTROL_SOURCE_INVALID", "wrong digest refusal differs")
        else:
          raise RuntimeError("wrong source digest was accepted")
        require(name not in sys.modules, "wrong digest published a module")
    finally:
      sys.modules.clear()
      sys.modules.update(saved_modules)
      sys.path[:] = saved_path
    require(
      tuple(sys.path) == ORIGINAL_SYS_PATH
      and set(sys.modules) == set(saved_modules)
      and all(sys.modules[key] is module for key, module in saved_modules.items())
      and not any(Path(value).is_relative_to("/inputs") for value in sys.path),
      "wrong-digest probe changed the import state",
    )


def require_execution_policy() -> None:
  policy_node = function_node("operational_execution_policy")
  policy_function = runtime_function(subject, "operational_execution_policy")
  require(
    not policy_node.args.posonlyargs and not policy_node.args.args
    and policy_node.args.vararg is None and not policy_node.args.kwonlyargs
    and policy_node.args.kwarg is None,
    "operational execution policy accepts caller input",
  )
  require(
    policy_function.__code__.co_argcount == 0
    and policy_function.__code__.co_kwonlyargcount == 0,
    "operational execution policy runtime signature differs",
  )
  policy = policy_function()
  parameters = getattr(subject.ExecutionPolicy, "__dataclass_params__", None)
  require(
    isinstance(policy, subject.ExecutionPolicy)
    and parameters is not None and parameters.frozen is True
    and tuple(subject.ExecutionPolicy.__dataclass_fields__) == (
      "command", "environment", "task_bindings", "uid", "gid", "cwd", "umask",
      "runtime_mounts", "fixed_sandbox_mounts", "task_inputs", "read_only_mounts",
      "planned_children", "control_seconds", "child_seconds", "workload_seconds",
      "outer_seconds", "mode",
    ),
    "execution policy is not the exact frozen dataclass",
  )
  expected = {
    "command": PRODUCTION_COMMAND,
    "environment": PRODUCTION_ENVIRONMENT,
    "task_bindings": PRODUCTION_BINDINGS,
    "uid": 1001,
    "gid": 1001,
    "cwd": "/work",
    "umask": 0o077,
    "runtime_mounts": RUNTIME_MOUNTS,
    "fixed_sandbox_mounts": FIXED_SANDBOX_MOUNTS,
    "task_inputs": PRODUCTION_TASK_INPUTS,
    "read_only_mounts": PRODUCTION_READ_ONLY_MOUNTS,
    "planned_children": PLANNED_CHILDREN,
    "control_seconds": CONTROL_SECONDS,
    "child_seconds": CHILD_SECONDS,
    "workload_seconds": WORKLOAD_SECONDS,
    "outer_seconds": OUTER_SECONDS,
    "mode": "E_NO_CHANGE_OFFLINE",
  }
  require(
    {name: getattr(policy, name) for name in expected} == expected,
    "fixed execution policy differs",
  )


def require_bounded_collector() -> None:
  require(
    subject.OPERATIONAL_STDOUT_LIMITS == STDOUT_LIMITS
    and subject.OPERATIONAL_STDERR_LIMIT == STDERR_LIMIT
    and subject.OPERATIONAL_REPORT_LIMIT == REPORT_LIMIT
    and subject.OPERATIONAL_EMPTY_CONFIG_LIMIT == EMPTY_CONFIG_LIMIT
    and subject.OPERATIONAL_EARLY_STREAM_LIMIT == EARLY_STREAM_LIMIT
    and subject.OPERATIONAL_MAIN_STREAM_LIMIT == MAIN_STREAM_LIMIT
    and subject.OPERATIONAL_RECORD_FILES == RECORD_FILES
    and subject.OPERATIONAL_CONTROL_TREE_FILES == CONTROL_TREE_FILES
    and subject.OPERATIONAL_LOOKUP_TREE_FILES == LOOKUP_TREE_FILES
    and subject.OPERATIONAL_TREE_DIRECTORIES == TREE_DIRECTORIES
    and subject.OPERATIONAL_TREE_MAX_DEPTH == TREE_MAX_DEPTH
    and subject.OPERATIONAL_TREE_FILE_LIMIT == TREE_FILE_LIMIT
    and subject.OPERATIONAL_TREE_AGGREGATE_LIMIT == TREE_AGGREGATE_LIMIT
    and subject.OPERATIONAL_RECORD_ROOT == OPERATIONAL_RECORD_ROOT
    and subject.SEMANTIC_OPERATIONAL_PATHS == OPERATIONAL_PATHS,
    "operational output caps differ",
  )
  for name in (
    "_read_bounded_operational_file", "_operational_record_path",
    "_validate_operational_record_root", "_bounded_operational_tree",
    "_collect_operational_outputs", "_structural_identity", "_sha256",
  ):
    runtime_function(subject, name)


def expect_operational_invalid(action: Callable[[], object]) -> None:
  try:
    action()
  except subject.RecipeError as error:
    require(str(error) == "E_CONTROL_OPERATIONAL_INVALID", "operational refusal differs")
  else:
    raise RuntimeError("invalid operational fixture was accepted")


def fixture_directory(name: str, mode: int = 0o700) -> Path:
  path = META / name
  path.mkdir(mode=mode)
  if stat.S_IMODE(path.lstat().st_mode) != mode:
    path.chmod(mode)
  return path


def fixture_file(path: Path, raw: bytes, mode: int = 0o600) -> None:
  descriptor = os.open(
    path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, mode,
  )
  with os.fdopen(descriptor, "wb") as stream:
    stream.write(raw)
  if stat.S_IMODE(path.lstat().st_mode) != mode:
    path.chmod(mode)


def expect_source_invalid(action: Callable[[], object]) -> None:
  try:
    action()
  except subject.RecipeError as error:
    require(str(error) == "E_CONTROL_SOURCE_INVALID", "source fixture refusal differs")
  else:
    raise RuntimeError("invalid fixed source fixture was accepted")


def fixed_loader_fixture_probe() -> None:
  root = fixture_directory("fixed-loader-fixtures")
  loader = runtime_function(subject, "_load_fixed_source")
  saved_modules = dict(sys.modules)
  saved_path = tuple(sys.path)
  positive = root / "positive.py"
  positive_raw = b"VALUE = 1\n"
  fixture_file(positive, positive_raw)
  positive_name = "e_control_fixed_loader_positive_probe"
  try:
    module = loader(positive_name, str(positive), sha256(positive_raw))
    require(
      module is sys.modules[positive_name]
      and module.__file__ == str(positive)
      and module.VALUE == 1,
      "fixed source loader did not execute the exact authenticated positive bytes",
    )
  finally:
    sys.modules.clear()
    sys.modules.update(saved_modules)
    sys.path[:] = saved_path

  wrong_mode = root / "wrong-mode.py"
  fixture_file(wrong_mode, positive_raw, 0o644)
  hardlink = root / "hardlink.py"
  hardlink_alias = root / "hardlink-alias.py"
  fixture_file(hardlink, positive_raw)
  os.link(hardlink, hardlink_alias, follow_symlinks=False)
  symlink = root / "symlink.py"
  os.symlink(positive.name, symlink)
  overflow = root / "overflow.py"
  overflow_raw = b"#" * (128 * 1024 + 1)
  fixture_file(overflow, overflow_raw)
  fixtures = (
    ("e_control_fixed_loader_mode_probe", wrong_mode, positive_raw),
    ("e_control_fixed_loader_hardlink_probe", hardlink, positive_raw),
    ("e_control_fixed_loader_symlink_probe", symlink, positive_raw),
    ("e_control_fixed_loader_overflow_probe", overflow, overflow_raw),
  )
  try:
    for name, path, raw in fixtures:
      expect_source_invalid(lambda name=name, path=path, raw=raw: loader(
        name, str(path), sha256(raw),
      ))
      require(name not in sys.modules, "invalid fixed source fixture published a module")
  finally:
    sys.modules.clear()
    sys.modules.update(saved_modules)
    sys.path[:] = saved_path
  require(
    tuple(sys.path) == ORIGINAL_SYS_PATH
    and set(sys.modules) == set(saved_modules)
    and all(sys.modules[name] is module for name, module in saved_modules.items()),
    "fixed source fixture probe did not restore the full import state",
  )


def expected_tree_state(
  root: Path,
  directories: tuple[Path, ...],
  files: dict[Path, bytes],
) -> object:
  directory_states = {
    str(relative): identity((root / relative).lstat())[:5] for relative in directories
  }
  file_states = {
    str(relative): subject.FileState(identity((root / relative).lstat()), sha256(raw))
    for relative, raw in files.items()
  }
  return subject.TreeState(directory_states, file_states)


def bounded_reader_fixture_probe() -> None:
  root = fixture_directory("reader-fixtures")
  positive = root / "positive"
  fixture_file(positive, b"bounded")
  require(
    subject._read_bounded_operational_file(positive, 7) == b"bounded",
    "bounded reader did not return the exact positive bytes",
  )
  empty = root / "empty"
  fixture_file(empty, b"")
  require(
    subject._read_bounded_operational_file(empty, 1) == b"",
    "bounded reader did not return the exact empty bytes",
  )
  overflow = root / "overflow"
  fixture_file(overflow, b"abc")
  expect_operational_invalid(
    lambda: subject._read_bounded_operational_file(overflow, 2)
  )
  wrong_mode = root / "wrong-mode"
  fixture_file(wrong_mode, b"x", 0o644)
  expect_operational_invalid(
    lambda: subject._read_bounded_operational_file(wrong_mode, 1)
  )
  hardlink_source = root / "hardlink-source"
  hardlink_alias = root / "hardlink-alias"
  fixture_file(hardlink_source, b"x")
  os.link(hardlink_source, hardlink_alias, follow_symlinks=False)
  expect_operational_invalid(
    lambda: subject._read_bounded_operational_file(hardlink_source, 1)
  )
  symlink = root / "symlink"
  os.symlink(positive.name, symlink)
  expect_operational_invalid(
    lambda: subject._read_bounded_operational_file(symlink, 7)
  )
  directory = fixture_directory("reader-fixtures-directory")
  expect_operational_invalid(
    lambda: subject._read_bounded_operational_file(directory, 1)
  )
  expect_operational_invalid(
    lambda: subject._read_bounded_operational_file(Path("relative"), 1)
  )


def build_record_fixture(
  name: str,
  *,
  missing: bool = False,
  extra: bool = False,
  symlink: bool = False,
) -> tuple[Path, dict[Path, bytes]]:
  root = fixture_directory(name)
  files: dict[Path, bytes] = {}
  for index in range(PLANNED_CHILDREN):
    for suffix in ("stdout", "stderr", "json"):
      relative = Path(f"child-{index:03d}.{suffix}")
      if missing and index == PLANNED_CHILDREN - 1 and suffix == "json":
        continue
      raw = b"{}" if suffix == "json" else b""
      if symlink and index == PLANNED_CHILDREN - 1 and suffix == "json":
        os.symlink("child-000.stdout", root / relative)
      else:
        fixture_file(root / relative, raw)
        files[relative] = raw
  if extra:
    fixture_file(root / "unexpected", b"x")
  return root, files


def record_root_fixture_probe() -> None:
  original = subject.OPERATIONAL_RECORD_ROOT
  valid, valid_files = build_record_fixture("record-root-valid")
  try:
    subject.OPERATIONAL_RECORD_ROOT = str(valid)
    for index in (0, 1, PLANNED_CHILDREN - 1):
      for suffix in ("stdout", "stderr", "json"):
        require(
          subject._operational_record_path(index, suffix)
          == valid / f"child-{index:03d}.{suffix}",
          "indexed operational record path differs",
        )
    expected = expected_tree_state(valid, (Path("."),), valid_files)
    actual = subject._validate_operational_record_root()
    require(actual == expected, "record-root validator returned a different exact tree")
    for action in (
      lambda: subject._operational_record_path(-1, "stdout"),
      lambda: subject._operational_record_path(PLANNED_CHILDREN, "stdout"),
      lambda: subject._operational_record_path(0, "bad"),
    ):
      expect_operational_invalid(action)
  finally:
    subject.OPERATIONAL_RECORD_ROOT = original
  for name, options in (
    ("record-root-missing", {"missing": True}),
    ("record-root-extra", {"extra": True}),
    ("record-root-symlink", {"symlink": True}),
  ):
    root, _ = build_record_fixture(name, **options)
    try:
      subject.OPERATIONAL_RECORD_ROOT = str(root)
      expect_operational_invalid(subject._validate_operational_record_root)
    finally:
      subject.OPERATIONAL_RECORD_ROOT = original
  require(subject.OPERATIONAL_RECORD_ROOT == original, "record-root fixture leaked its redirect")


def call_bounded_tree(
  root: Path,
  *,
  files: int,
  directories: int,
  depth: int = 4,
  per_file: int = 16,
  aggregate: int = 64,
) -> object:
  return subject._bounded_operational_tree(
    root,
    expected_files=files,
    expected_directories=directories,
    max_depth=depth,
    per_file_limit=per_file,
    aggregate_limit=aggregate,
  )


def bounded_tree_fixture_probe() -> None:
  root = fixture_directory("tree-valid")
  child = root / "child"
  child.mkdir(mode=0o700)
  files = {Path("one"): b"one", Path("child/two"): b"two"}
  for relative, raw in files.items():
    fixture_file(root / relative, raw)
  expected = expected_tree_state(root, (Path("."), Path("child")), files)
  require(
    call_bounded_tree(root, files=2, directories=2) == expected,
    "bounded tree did not return the exact positive tree",
  )
  expect_operational_invalid(
    lambda: call_bounded_tree(Path("relative"), files=0, directories=0)
  )

  extra_file = fixture_directory("tree-extra-file")
  fixture_file(extra_file / "one", b"1")
  fixture_file(extra_file / "two", b"2")
  expect_operational_invalid(
    lambda: call_bounded_tree(extra_file, files=1, directories=1)
  )
  missing_file = fixture_directory("tree-missing-file")
  fixture_file(missing_file / "one", b"1")
  expect_operational_invalid(
    lambda: call_bounded_tree(missing_file, files=2, directories=1)
  )
  extra_directory = fixture_directory("tree-extra-directory")
  (extra_directory / "child").mkdir(mode=0o700)
  expect_operational_invalid(
    lambda: call_bounded_tree(extra_directory, files=0, directories=1)
  )
  missing_directory = fixture_directory("tree-missing-directory")
  expect_operational_invalid(
    lambda: call_bounded_tree(missing_directory, files=0, directories=2)
  )

  deep = fixture_directory("tree-depth")
  (deep / "one").mkdir(mode=0o700)
  (deep / "one/two").mkdir(mode=0o700)
  fixture_file(deep / "one/two/leaf", b"x")
  expect_operational_invalid(
    lambda: call_bounded_tree(deep, files=1, directories=3, depth=1)
  )
  large = fixture_directory("tree-per-file")
  fixture_file(large / "large", b"abc")
  expect_operational_invalid(
    lambda: call_bounded_tree(large, files=1, directories=1, per_file=2)
  )
  aggregate = fixture_directory("tree-aggregate")
  fixture_file(aggregate / "one", b"ab")
  fixture_file(aggregate / "two", b"cd")
  expect_operational_invalid(
    lambda: call_bounded_tree(
      aggregate, files=2, directories=1, per_file=2, aggregate=3,
    )
  )
  symlink = fixture_directory("tree-symlink")
  fixture_file(symlink / "target", b"x")
  os.symlink("target", symlink / "alias")
  expect_operational_invalid(
    lambda: call_bounded_tree(symlink, files=2, directories=1)
  )
  hardlink = fixture_directory("tree-hardlink")
  fixture_file(hardlink / "source", b"x")
  os.link(hardlink / "source", hardlink / "alias", follow_symlinks=False)
  expect_operational_invalid(
    lambda: call_bounded_tree(hardlink, files=2, directories=1)
  )
  wrong_file_mode = fixture_directory("tree-file-mode")
  fixture_file(wrong_file_mode / "leaf", b"x", 0o644)
  expect_operational_invalid(
    lambda: call_bounded_tree(wrong_file_mode, files=1, directories=1)
  )
  wrong_directory_mode = fixture_directory("tree-directory-mode", 0o755)
  expect_operational_invalid(
    lambda: call_bounded_tree(wrong_directory_mode, files=0, directories=1)
  )


def collector_spy_probe() -> None:
  runner_paths = tuple(OPERATIONAL_PATHS)
  runner_children = int(PLANNED_CHILDREN)
  runner_stdout_limits = tuple(STDOUT_LIMITS)
  runner_stderr_limit = int(STDERR_LIMIT)
  runner_report_limit = int(REPORT_LIMIT)
  runner_empty_limit = int(EMPTY_CONFIG_LIMIT)
  runner_early_limit = int(EARLY_STREAM_LIMIT)
  runner_main_limit = int(MAIN_STREAM_LIMIT)
  runner_record_files = int(RECORD_FILES)
  runner_control_files = int(CONTROL_TREE_FILES)
  runner_lookup_files = int(LOOKUP_TREE_FILES)
  runner_directories = int(TREE_DIRECTORIES)
  runner_depth = int(TREE_MAX_DEPTH)
  runner_file_limit = int(TREE_FILE_LIMIT)
  runner_aggregate_limit = int(TREE_AGGREGATE_LIMIT)
  read_calls: list[tuple[Path, int]] = []
  validator_calls: list[None] = []
  tree_calls: list[tuple[Path, int, int, int, int, int]] = []
  record_state = subject.TreeState({"record": (1, 2, 3, 4, 5)}, {})
  control_state = subject.TreeState({"control": (6, 7, 8, 9, 10)}, {})
  lookup_state = subject.TreeState({"lookup": (11, 12, 13, 14, 15)}, {})
  policy_names = (
    "OPERATIONAL_RECORD_ROOT", "CONTROL_ROOT", "LOOKUP_ROOT", "EMPTY_CONFIG",
    "EARLY_PATH", "MAIN_PATH", "SEMANTIC_OPERATIONAL_PATHS", "SEMANTIC_RECORDS",
    "OPERATIONAL_STDOUT_LIMITS", "OPERATIONAL_STDERR_LIMIT",
    "OPERATIONAL_REPORT_LIMIT", "OPERATIONAL_EMPTY_CONFIG_LIMIT",
    "OPERATIONAL_EARLY_STREAM_LIMIT", "OPERATIONAL_MAIN_STREAM_LIMIT",
    "OPERATIONAL_RECORD_FILES", "OPERATIONAL_CONTROL_TREE_FILES",
    "OPERATIONAL_LOOKUP_TREE_FILES", "OPERATIONAL_TREE_DIRECTORIES",
    "OPERATIONAL_TREE_MAX_DEPTH", "OPERATIONAL_TREE_FILE_LIMIT",
    "OPERATIONAL_TREE_AGGREGATE_LIMIT",
  )
  frozen_policy = tuple((name, getattr(subject, name)) for name in policy_names)
  expected_policy = (
    ("OPERATIONAL_RECORD_ROOT", runner_paths[0]),
    ("CONTROL_ROOT", runner_paths[1]),
    ("LOOKUP_ROOT", runner_paths[2]),
    ("EMPTY_CONFIG", runner_paths[3]),
    ("EARLY_PATH", runner_paths[4]),
    ("MAIN_PATH", runner_paths[5]),
    ("SEMANTIC_OPERATIONAL_PATHS", runner_paths),
    ("SEMANTIC_RECORDS", runner_children),
    ("OPERATIONAL_STDOUT_LIMITS", runner_stdout_limits),
    ("OPERATIONAL_STDERR_LIMIT", runner_stderr_limit),
    ("OPERATIONAL_REPORT_LIMIT", runner_report_limit),
    ("OPERATIONAL_EMPTY_CONFIG_LIMIT", runner_empty_limit),
    ("OPERATIONAL_EARLY_STREAM_LIMIT", runner_early_limit),
    ("OPERATIONAL_MAIN_STREAM_LIMIT", runner_main_limit),
    ("OPERATIONAL_RECORD_FILES", runner_record_files),
    ("OPERATIONAL_CONTROL_TREE_FILES", runner_control_files),
    ("OPERATIONAL_LOOKUP_TREE_FILES", runner_lookup_files),
    ("OPERATIONAL_TREE_DIRECTORIES", runner_directories),
    ("OPERATIONAL_TREE_MAX_DEPTH", runner_depth),
    ("OPERATIONAL_TREE_FILE_LIMIT", runner_file_limit),
    ("OPERATIONAL_TREE_AGGREGATE_LIMIT", runner_aggregate_limit),
  )
  require(frozen_policy == expected_policy, "collector policy differs before the spy")

  def read_spy(path: Path, limit: int) -> bytes:
    require(isinstance(path, Path) and type(limit) is int, "collector changed reader arguments")
    read_calls.append((path, limit))
    return f"{path}\0{limit}".encode("ascii")

  def validator_spy() -> object:
    validator_calls.append(None)
    return record_state

  def tree_spy(
    root: Path,
    *,
    expected_files: int,
    expected_directories: int,
    max_depth: int,
    per_file_limit: int,
    aggregate_limit: int,
  ) -> object:
    tree_calls.append((
      root, expected_files, expected_directories, max_depth, per_file_limit,
      aggregate_limit,
    ))
    if root == Path(runner_paths[1]):
      return control_state
    if root == Path(runner_paths[2]):
      return lookup_state
    raise RuntimeError("collector requested an unapproved tree")

  names = (
    "_read_bounded_operational_file", "_validate_operational_record_root",
    "_bounded_operational_tree",
  )
  originals = {name: getattr(subject, name) for name in names}
  collector = runtime_function(subject, "_collect_operational_outputs")
  try:
    subject._read_bounded_operational_file = read_spy
    subject._validate_operational_record_root = validator_spy
    subject._bounded_operational_tree = tree_spy
    raw = collector()
    require(
      tuple((name, getattr(subject, name)) for name in policy_names)
      == frozen_policy == expected_policy,
      "collector mutated a fixed policy or path global",
    )
  finally:
    for name, value in originals.items():
      setattr(subject, name, value)

  require(
    all(getattr(subject, name) is value for name, value in originals.items()),
    "collector spy did not restore only the mocked helpers",
  )
  record_root = Path(runner_paths[0])
  expected_record_calls = [
    (record_root / f"child-{index:03d}.{suffix}", limit)
    for index in range(runner_children)
    for suffix, limit in (
      ("stdout", runner_stdout_limits[index]),
      ("stderr", runner_stderr_limit),
      ("json", runner_report_limit),
    )
  ]
  fixed_calls = [
    (Path(runner_paths[3]), runner_empty_limit),
    (Path(runner_paths[4]), runner_early_limit),
    (Path(runner_paths[5]), runner_main_limit),
  ]
  require(
    len(read_calls) == runner_children * 3 + 3
    and [call for call in read_calls if call[0].parent == record_root]
    == expected_record_calls
    and sorted(
      (str(path), limit) for path, limit in read_calls if path.parent != record_root
    ) == sorted((str(path), limit) for path, limit in fixed_calls),
    "collector did not make the exact bounded record and fixed reads",
  )
  expected_records = tuple(
    tuple(f"{path}\0{limit}".encode("ascii") for path, limit in expected_record_calls[offset:offset + 3])
    for offset in range(0, len(expected_record_calls), 3)
  )
  expected_paths = runner_paths
  require(
    validator_calls == [None]
    and tree_calls == [
      (
        Path(runner_paths[1]), runner_control_files, runner_directories,
        runner_depth, runner_file_limit, runner_aggregate_limit,
      ),
      (
        Path(runner_paths[2]), runner_lookup_files, runner_directories,
        runner_depth, runner_file_limit, runner_aggregate_limit,
      ),
    ]
    and isinstance(raw, subject.RawControlFiles)
    and tuple(subject.RawControlFiles.__dataclass_fields__) == (
      "paths", "record_state", "records", "control_state", "lookup_state",
      "empty_config_raw", "early_raw", "main_raw",
    )
    and raw.paths == expected_paths
    and raw.record_state is record_state and raw.records == expected_records
    and raw.control_state is control_state and raw.lookup_state is lookup_state
    and raw.empty_config_raw == f"{runner_paths[3]}\0{runner_empty_limit}".encode("ascii")
    and raw.early_raw == f"{runner_paths[4]}\0{runner_early_limit}".encode("ascii")
    and raw.main_raw == f"{runner_paths[5]}\0{runner_main_limit}".encode("ascii"),
    "collector did not wire the exact validator, trees, records, and RawControlFiles fields",
  )
  no_operational_outputs()


class EExecutionRedTests(unittest.TestCase):
  def test_a_fixed_self_bootstrap_is_missing(self) -> None:
    pure_setup_checks()
    self.assertTrue(
      hasattr(subject, "_bootstrap_fixed_sources")
      and hasattr(subject, "_load_fixed_source")
      and hasattr(subject, "_fixed_source_identity")
      and hasattr(subject, "FIXED_SOURCE_BYTES")
      and hasattr(subject, "FIXED_SOURCE_INPUTS"),
      "fixed five-source self-bootstrap is missing",
    )
    require_fixed_self_bootstrap()
    direct_import_probe()
    partial_import_probe()
    wrong_digest_probe()
    fixed_loader_fixture_probe()
    closed_operational_apis(subject)
    no_operational_outputs()

  def test_b_exact_execution_policy_is_missing(self) -> None:
    pure_setup_checks()
    operational_contract_mutation_probe()
    operational_publication_fault_shape_probe()
    self.assertTrue(
      hasattr(subject, "ExecutionPolicy")
      and hasattr(subject, "operational_execution_policy"),
      "exact eight-input isolated ExecutionPolicy is missing",
    )
    require_execution_policy()
    closed_operational_apis(subject)
    no_operational_outputs()

  def test_c_bounded_operational_collector_is_missing(self) -> None:
    pure_setup_checks()
    self.assertTrue(
      hasattr(subject, "OPERATIONAL_STDOUT_LIMITS")
      and hasattr(subject, "OPERATIONAL_STDERR_LIMIT")
      and hasattr(subject, "OPERATIONAL_REPORT_LIMIT")
      and hasattr(subject, "OPERATIONAL_EMPTY_CONFIG_LIMIT")
      and hasattr(subject, "OPERATIONAL_EARLY_STREAM_LIMIT")
      and hasattr(subject, "OPERATIONAL_MAIN_STREAM_LIMIT")
      and hasattr(subject, "OPERATIONAL_RECORD_FILES")
      and hasattr(subject, "OPERATIONAL_CONTROL_TREE_FILES")
      and hasattr(subject, "OPERATIONAL_LOOKUP_TREE_FILES")
      and hasattr(subject, "OPERATIONAL_TREE_DIRECTORIES")
      and hasattr(subject, "OPERATIONAL_TREE_MAX_DEPTH")
      and hasattr(subject, "OPERATIONAL_TREE_FILE_LIMIT")
      and hasattr(subject, "OPERATIONAL_TREE_AGGREGATE_LIMIT")
      and hasattr(subject, "OPERATIONAL_RECORD_ROOT")
      and hasattr(subject, "_read_bounded_operational_file")
      and hasattr(subject, "_operational_record_path")
      and hasattr(subject, "_validate_operational_record_root")
      and hasattr(subject, "_bounded_operational_tree")
      and hasattr(subject, "_collect_operational_outputs"),
      "explicitly bounded fixed operational collector is missing",
    )
    require_bounded_collector()
    collector_spy_probe()
    bounded_reader_fixture_probe()
    record_root_fixture_probe()
    bounded_tree_fixture_probe()
    closed_operational_apis(subject)
    no_operational_outputs()


def write_json(path: Path, value: object) -> None:
  descriptor = os.open(
    path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600,
  )
  with os.fdopen(descriptor, "wb") as stream:
    stream.write(
      (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
      .encode("ascii")
    )


def main() -> int:
  try:
    os.umask(0o077)
    pure_setup_checks()
    META.mkdir(mode=0o700)
    write_json(META / "setup.json", {
      "setup": "PASS",
      "subject_sha256": SUBJECT_SHA256,
      "test_task_inputs": TEST_TASK_INPUTS,
      "test_read_only_mounts": TEST_READ_ONLY_MOUNTS,
      "production_task_inputs": PRODUCTION_TASK_INPUTS,
      "production_read_only_mounts": PRODUCTION_READ_ONLY_MOUNTS,
      "planned_children": PLANNED_CHILDREN,
      "children_executed": 0,
      "operational_control_proved": False,
      "fresh_control_proved": False,
      "image_created": False,
      "module_loaded": False,
      "staged": False,
      "booted": False,
    })
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  print(
    "SETUP PASS: nine-input GREEN harness proves eight-input/593-mount production plan; "
    "zero workload children",
    flush=True,
  )
  program = unittest.main(argv=sys.argv, verbosity=2, exit=False)
  result = program.result
  try:
    validate_binding_tree()
    for path in PINS:
      raw, after = read_pinned(path)
      require(raw == INPUT_BYTES[path] and after == INPUT_STATES[path], "immutable input changed")
    indexes, directory_state, file_states = read_index_directory()
    require(
      indexes == INDEX_BYTES
      and directory_state == INDEX_STATE
      and file_states == INDEX_FILE_STATES,
      "index input directory changed",
    )
    require(
      result.testsRun == 3
      and not result.failures
      and not result.errors
      and not result.skipped,
      "result is not the exact three controlled GREEN passes",
    )
    no_operational_outputs()
    write_json(META / "test-result.json", {
      "setup": "PASS",
      "tests": result.testsRun,
      "failures": len(result.failures),
      "errors": len(result.errors),
      "skipped": len(result.skipped),
      "failed_tests": [test.id() for test, _ in result.failures],
      "error_tests": [test.id() for test, _ in result.errors],
      "subject_sha256": SUBJECT_SHA256,
      "inputs_unchanged": True,
      "test_task_inputs": TEST_TASK_INPUTS,
      "test_read_only_mounts": TEST_READ_ONLY_MOUNTS,
      "production_task_inputs": PRODUCTION_TASK_INPUTS,
      "production_read_only_mounts": PRODUCTION_READ_ONLY_MOUNTS,
      "planned_children": PLANNED_CHILDREN,
      "children_executed": 0,
      "real_result_present": Path("/work/e-control-result.json").exists(),
      "operational_control_proved": False,
      "fresh_control_proved": False,
      "image_created": False,
      "module_loaded": False,
      "staged": False,
      "booted": False,
    })
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"POSTCHECK FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
