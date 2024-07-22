#
# Copyright 2024 Canonical, Ltd.
#

import logging
from pathlib import Path

from k8s_test_harness import harness
from k8s_test_harness.util import env_util, k8s_util

LOG = logging.getLogger(__name__)


def _clone_git_repo(location: Path, repo: str, branch: str, instance: harness.Instance):
    location.mkdir()

    clone_command = [
        "git",
        "clone",
        repo,
        "--branch",
        branch,
        "--depth",
        "1",
        str(location.absolute()),
    ]

    instance.exec(clone_command)


def _deploy_sriov_ndp(temp_path: Path, instance: harness.Instance):
    rock = env_util.get_build_meta_info_for_rock_version(
        "sriov-net-device-plugin", "3.6.2", "amd64"
    )

    clone_path = temp_path / "sriov-ndp"
    repo = "https://github.com/k8snetworkplumbingwg/sriov-network-device-plugin"
    _clone_git_repo(clone_path, repo, "v3.6.2", instance)
    deployments_path = clone_path / "deployments"

    # Create a NetworkAttachmentDefinition and a deployment requiring it.
    for filename in ["configMap.yaml", "sriov-crd.yaml"]:
        manifest = deployments_path / filename
        instance.exec(
            ["k8s", "kubectl", "apply", "-f", "-"],
            input=Path(manifest).read_bytes(),
        )

    # We need to replace the daemonset's image with our own rock image.
    daemonset = Path(deployments_path / "sriovdp-daemonset.yaml").read_text()
    daemonset = daemonset.replace(
        "ghcr.io/k8snetworkplumbingwg/sriov-network-device-plugin:latest-amd64",
        rock.image,
        1,
    )
    instance.exec(
        ["k8s", "kubectl", "apply", "-f", "-"],
        input=daemonset.encode(),
    )


def test_integration_sriov_ndp(tmp_path: Path, module_instance: harness.Instance):
    # We also need multus in order to test out sriov-network-device-plugin.
    # It should become Available if everything is fine with it.
    helm_cmd = k8s_util.get_helm_install_command(
        "multus", "oci://registry-1.docker.io/bitnamicharts/multus-cni"
    )
    module_instance.exec(helm_cmd)
    k8s_util.wait_for_daemonset(module_instance, "multus-multus-cni", "kube-system")

    _deploy_sriov_ndp(tmp_path, module_instance)
    k8s_util.wait_for_daemonset(
        module_instance, "kube-sriov-device-plugin-amd64", "kube-system"
    )
