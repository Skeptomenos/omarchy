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
SUBJECT_SHA256 = "70f369f87942b6ca6826c808536353ae0cc400123204040b9c005995ab43c3e3"
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
   "abbf59410a05fd5c789820df3d40e59d0a5c33cf1204ab93c7aeef806da7b1df"),
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
  ("function:command_plan", "7a8a7afbefec73373aeeb6e178c777ba0f05ed0f20dcef17643e031b9919c688"),
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
  ("function:_semantic_command_plan", "685423efce6cb280c5df2219cb64819896b6f1e49b56a4624d09d57f5e7e6ea6"),
  ("function:_semantic_command_observation", "b6e315c79f55c619581814507bc08799eb4afc8036743e90bbd1847f6419f387"),
  ("function:_semantic_identity_records", "fd125fbf978e706f8db088c5020f104e80bdab36ebf2e4f234b4207c64a89627"),
  ("function:_semantic_bound_observation", "9714413167510e0cfe8607247c66e76dc5c1e0622157491cdb7c9cdff110d830"),
  ("function:_semantic_archive_records", "630968c9723a8e894690c3cc3b0b7b10560af477a9227b8b8a679c15a022e483"),
  ("function:_semantic_aggregate", "5b6ff7819d4119034ed6daea4ea5afe1bd0846efbcdb53cbeeb91c71957f5dde"),
  ("function:_validate_file_metadata", "9d36cd1ff10327e9e8855e262d898edff5eee27baadeffccacbc23b6078ced67"),
  ("function:_validate_file_content", "9505e713f4625b185e30d100d8199d049db609bc25a70a2f16aa686359baae29"),
  ("function:_validate_command_shape", "fdeadd417ab56d391f2e4c1fad50909d70b51eb30318396d7a7c447e4d3f89ec"),
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
  ("function:finalize_structural_result", "67a4ba2ab536e08615b16e41ef6e1d4a472202162272191330386dbd5c6a6ff5"),
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
  ("e_control", "/inputs/subject/e_control.py", "abbf59410a05fd5c789820df3d40e59d0a5c33cf1204ab93c7aeef806da7b1df"),
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
  _require(type(root) is Path and root.is_absolute(), "E_CONTROL_OPERATIONAL_INVALID")
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


def pre_vet_subject(raw: bytes) -> tuple[ast.Module, bool]:
  tree = ast.parse(raw, filename=str(SUBJECT), mode="exec")
  actual = node_manifest(tree.body)
  if actual == BASELINE_TOP_LEVEL_MANIFEST:
    return tree, False
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
  for name in ("operational_policy", "finalize_operational_result", "main"):
    function = runtime_function(module, name)
    try:
      function()
    except module.RecipeError as error:
      require(str(error) == "E_CONTROL_RECIPE_UNAVAILABLE", f"{name} refusal differs")
    else:
      raise RuntimeError(f"{name} is not closed")


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
  plan.append(("/usr/bin/gzip",))
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
  for name in ("operational_policy", "finalize_operational_result", "main"):
    node = function_node(name)
    require(len(node.body) == 2 and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str),
            f"{name} must contain only its docstring and refusal")
    refusal = node.body[1]
    require(
      isinstance(refusal, ast.Raise)
      and refusal.cause is None
      and isinstance(refusal.exc, ast.Call)
      and isinstance(refusal.exc.func, ast.Name)
      and refusal.exc.func.id == "RecipeError"
      and len(refusal.exc.args) == 1
      and isinstance(refusal.exc.args[0], ast.Constant)
      and refusal.exc.args[0].value == "E_CONTROL_RECIPE_UNAVAILABLE"
      and not refusal.exc.keywords,
      f"{name} is not an unconditional one-statement refusal",
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
    require(type(path) is Path and type(limit) is int, "collector changed reader arguments")
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
    "SETUP PASS: nine-input RED harness proves eight-input/593-mount production plan; "
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
    failed_tests = [test.id().removeprefix("__main__.") for test, _ in result.failures]
    require(
      result.testsRun == 3
      and len(result.failures) == 3
      and not result.errors
      and not result.skipped
      and failed_tests == list(SELECTED_TESTS),
      "result is not the exact three controlled assertion REDs",
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
  return 1


if __name__ == "__main__":
  raise SystemExit(main())
