#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import paramiko


def getenv(name, required=False, default=None):
    val = os.getenv(name, default)
    if required and (val is None or str(val).strip() == ""):
        print(f"[ERR] Missing required env var: {name}", file=sys.stderr)
        sys.exit(2)
    return val


def main():
    host = getenv("SSH_HOST", required=True)
    user = getenv("SSH_USER", required=True)
    password = getenv("SSH_PASSWORD", required=True)
    remote_cmd = getenv("SSH_COMMAND_4", required=True)

    port = int(getenv("SSH_PORT", "22"))
    timeout = int(getenv("SSH_TIMEOUT", "60"))

    client = paramiko.SSHClient()
    # se vuoi bloccare host key sconosciute, puoi cambiare in RejectPolicy
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=user,
            password=password,
            timeout=timeout,
            banner_timeout=timeout,
            auth_timeout=timeout,
            look_for_keys=False,
            allow_agent=False,
        )

        chan = client.get_transport().open_session()
        chan.exec_command(remote_cmd)

        # streaming stdout/stderr
        while True:
            did_io = False
            if chan.recv_ready():
                data = chan.recv(4096).decode(errors="replace")
                if data:
                    print(data, end="", flush=True)
                    did_io = True
            if chan.recv_stderr_ready():
                data = chan.recv_stderr(4096).decode(errors="replace")
                if data:
                    print(data, end="", flush=True, file=sys.stderr)
                    did_io = True
            if chan.exit_status_ready() and not chan.recv_ready() and not chan.recv_stderr_ready():
                break
            if not did_io:
                time.sleep(0.05)

        exit_code = chan.recv_exit_status()
        chan.close()
        client.close()
        sys.exit(exit_code)

    except paramiko.AuthenticationException:
        print("[ERR] Authentication failed (username/password).", file=sys.stderr)
        sys.exit(10)
    except Exception as e:
        print(f"[ERR] SSH error: {e}", file=sys.stderr)
        sys.exit(11)
    finally:
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
