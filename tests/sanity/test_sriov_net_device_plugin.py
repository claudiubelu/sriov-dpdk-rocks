#
# Copyright 2024 Canonical, Ltd.
#

from k8s_test_harness.util import docker_util, env_util

ROCK_EXPECTED_FILES = [
    "/entrypoint.sh",
    "/usr/bin/ddptool",
    "/usr/bin/sriovdp",
]


def test_sriov_dpdk_rock():
    """Test SRIOV Network Device Plugin rock."""

    rock = env_util.get_build_meta_info_for_rock_version(
        "sriov-net-device-plugin", "3.6.2", "amd64"
    )
    image = rock.image

    # check rock filesystem.
    docker_util.ensure_image_contains_paths(image, ROCK_EXPECTED_FILES)

    # check binary.
    process = docker_util.run_in_docker(image, ["sriovdp", "--help"], False)
    assert "Usage of sriovdp:" in process.stderr

    # check ddptool and version.
    process = docker_util.run_in_docker(image, ["ddptool", "--version"], False)
    assert "DDPTool version 1.0.1.12" in process.stdout

    # check /entrypoint.sh script.
    process = docker_util.run_in_docker(image, ["/entrypoint.sh"], False)
    assert "open /etc/pcidp/config.json: no such file or directory" in process.stderr
