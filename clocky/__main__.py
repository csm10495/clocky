import argparse
import io
import mmap
import os
import pathlib
import shlex
import shutil
import statistics
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

import psutil

from . import __version__

GNU_TIME_DEFAULT_FORMAT_STRING = (
    "%Uuser %Ssystem %Eelapsed %PCPU (%Xtext+%Ddata %Mmax)k\n%Iinputs+%Ooutputs (%Fmajor+%Rminor)pagefaults %Wswaps"
)


@dataclass
class ProcessInfo:
    last_cpu_time: Optional[psutil._common.pcputimes]
    memory_infos: list
    last_io_counters: Optional[psutil._common.pio]
    run_time: float
    exit_code: int
    last_ctx_switches: Optional[psutil._common.pctxsw]
    cmd: List[str]

    def get_user_time(self) -> float:
        return self.last_cpu_time.user if self.last_cpu_time else 0

    def get_sys_time(self) -> float:
        return self.last_cpu_time.system if self.last_cpu_time else 0

    def get_percentage_of_cpu_this_job_got(self) -> int:
        return int((self.get_user_time() + self.get_sys_time()) / self.run_time) * 100

    def get_max_resident_set_size_in_kilobytes(self) -> int:
        if not self.memory_infos:
            return 0

        return int(round(max([a.rss for a in self.memory_infos]) / 1024))

    def get_avg_resident_set_size_in_kilobytes(self) -> int:
        if not self.memory_infos:
            return 0

        return int(round(statistics.mean([a.rss for a in self.memory_infos]) / 1024))

    def get_avg_total_memory_usage_in_kilobytes(self) -> int:
        if not self.memory_infos:
            return 0

        return int(round(statistics.mean([a.uss for a in self.memory_infos]) / 1024))

    def get_avg_size_of_shared_text_space_in_kilobytes(self) -> int:
        if not self.memory_infos:
            return 0

        return int(round(statistics.mean([getattr(a, "shared", 0) for a in self.memory_infos]) / 1024))

    def get_number_of_page_faults(self) -> int:
        if not self.memory_infos:
            return 0

        attr = ""
        for i in ("num_page_faults", "pfaults"):
            if i in self.memory_infos[0]:
                attr = i
                break

        if not attr:
            return 0

        return max([getattr(a, attr) for a in self.memory_infos])

    def get_number_of_involuntary_context_switches(self) -> int:
        return self.last_ctx_switches.involuntary if self.last_ctx_switches else 0

    def get_number_of_voluntary_context_switches(self) -> int:
        return self.last_ctx_switches.voluntary if self.last_ctx_switches else 0

    def get_read_count(self) -> int:
        return self.last_io_counters.read_count if self.last_io_counters else 0

    def get_write_count(self) -> int:
        return self.last_io_counters.write_count if self.last_io_counters else 0

    @classmethod
    def get_page_size(cls) -> int:
        return mmap.PAGESIZE

    def __str__(self):
        """Used for verbose output"""
        return f"""Command being timed: {shlex.join(self.cmd)}
        User time (seconds): {self.get_user_time():.2f}
        System time (seconds): {self.get_sys_time():.2f}
        Percent of CPU this job got: {self.get_percentage_of_cpu_this_job_got()}%
        Elapsed (wall clock) time (h:mm:ss or m:ss): {seconds_to_time_str(self.run_time, gnu_elapsed_real_time=True)}
        Average shared text size (kbytes): {self.get_avg_size_of_shared_text_space_in_kilobytes()}
        Average unshared data size (kbytes): {self.get_avg_total_memory_usage_in_kilobytes()}
        Average stack size (kbytes): {self.get_avg_total_memory_usage_in_kilobytes()}
        Average total size (kbytes): {self.get_avg_total_memory_usage_in_kilobytes()}
        Maximum resident set size (kbytes): {self.get_max_resident_set_size_in_kilobytes()}
        Average resident set size (kbytes): {self.get_avg_resident_set_size_in_kilobytes()}
        Major (requiring I/O) page faults: {self.get_number_of_page_faults()}
        Minor (reclaiming a frame) page faults: ?
        Voluntary context switches: {self.get_number_of_voluntary_context_switches()}
        Involuntary context switches: {self.get_number_of_involuntary_context_switches()}
        Swaps: ?
        File system inputs: {self.get_read_count()}
        File system outputs: {self.get_write_count()}
        Socket messages sent: ?
        Socket messages received: ?
        Signals delivered: ?
        Page size (bytes): {self.get_page_size()}
        Exit status: {self.exit_code}
        """


def run(
    cmd: List[str],
    gnu_mode: bool = False,
    quiet: bool = False,
    output: io.TextIOBase = sys.stderr,
):
    run_time = 0
    next_counters_time = 0
    counter_time_sec = 0.01
    last_cpu_times = None
    last_ctx_switches = None
    memory_infos = []
    io_counters = None
    exit_code = 0

    if cmd:
        if shutil.which(cmd[0]):
            proc = psutil.Popen(cmd)

            while proc.is_running():
                if time.time() > next_counters_time:
                    try:
                        last_cpu_times = proc.cpu_times()
                        last_ctx_switches = proc.num_ctx_switches()
                        # technically we need all of these, but cheat if its becoming huge
                        if len(memory_infos) > 1_000_000:
                            del memory_infos[0]
                        memory_infos.append(proc.memory_full_info())
                        io_counters = proc.io_counters()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # process died... thats ok.
                        break

                    # reset counter time
                    next_counters_time = time.time() + counter_time_sec

                time.sleep(0.001)

            death_time = time.time()
            exit_code = proc.wait()
            run_time = death_time - proc.create_time()
        else:
            print(f"{cmd[0]}: command not found", file=output)

            # 127 == command not found
            exit_code = 127

    if not quiet and gnu_mode and exit_code != 0:
        print(f"Command exited with non-zero status {exit_code}", file=output)

    return ProcessInfo(
        last_cpu_times,
        memory_infos,
        io_counters,
        run_time,
        exit_code,
        last_ctx_switches,
        cmd,
    )


def seconds_to_time_str(secs: float, gnu_elapsed_real_time=False) -> str:
    """
    Takes the given number of seconds and converts it into a time string.

    If gnu_elapsed_real_time, return via the [hours:]minutes:seconds format.
    Otherwise, return via the [<hrs>h]<min>m<sec>s format
    """
    hours, remaining_sec_after_hour = divmod(secs, 3600)
    minutes, remaining_secs = divmod(remaining_sec_after_hour, 60)

    if gnu_elapsed_real_time:
        # this dot logic is funky.. but i can't figure out the right way to get
        # 0.0 to be 00.0 to match gnu format
        before_dot, after_dot = f"{remaining_secs:.2f}".split(".")
        if len(before_dot) == 1:
            before_dot = "0" + before_dot

        if hours:
            ret_str = f"{int(hours)}:{str(int(minutes)).zfill(2)}:{before_dot}.{after_dot}"
        else:
            ret_str = f"{int(minutes)}:{before_dot}.{after_dot}"
    else:
        if hours:
            ret_str = f"{int(hours)}h{int(minutes)}m{remaining_secs:.3f}s"
        else:
            ret_str = f"{int(minutes)}m{remaining_secs:.3f}s"

    return ret_str


def process_custom_format_str(format_str: str, process_info: ProcessInfo) -> str:
    ret_str = str(format_str)
    ret_str = ret_str.replace("%U", f"{process_info.get_user_time():.2f}")
    ret_str = ret_str.replace("%S", f"{process_info.get_sys_time():.2f}")
    ret_str = ret_str.replace(
        "%E",
        f"{seconds_to_time_str(process_info.run_time, gnu_elapsed_real_time=True)}",
    )
    ret_str = ret_str.replace("%e", f"{process_info.run_time:.2f}")
    ret_str = ret_str.replace("%M", f"{process_info.get_max_resident_set_size_in_kilobytes()}")
    ret_str = ret_str.replace("%t", f"{process_info.get_avg_resident_set_size_in_kilobytes()}")
    ret_str = ret_str.replace("%K", f"{process_info.get_avg_total_memory_usage_in_kilobytes()}")
    ret_str = ret_str.replace("%D", f"{process_info.get_avg_total_memory_usage_in_kilobytes()}")
    ret_str = ret_str.replace("%p", f"{process_info.get_avg_total_memory_usage_in_kilobytes()}")
    ret_str = ret_str.replace("%X", f"{process_info.get_avg_size_of_shared_text_space_in_kilobytes()}")
    ret_str = ret_str.replace("%Z", str(process_info.get_page_size()))
    ret_str = ret_str.replace("%F", f"{process_info.get_number_of_page_faults()}")
    # %R would be minor/recoverable page faults... can't currently get this via psutil
    ret_str = ret_str.replace("%R", "?")
    # %W would be number of times process was swapped out of main memory... can't currently get this via psutil
    ret_str = ret_str.replace("%W", "?")
    ret_str = ret_str.replace("%c", f"{process_info.get_number_of_involuntary_context_switches()}")
    ret_str = ret_str.replace("%w", f"{process_info.get_number_of_voluntary_context_switches()}")
    ret_str = ret_str.replace("%I", f"{process_info.get_read_count()}")
    ret_str = ret_str.replace("%O", f"{process_info.get_write_count()}")
    # %r is sockets recv'd... can't currently get this via psutil
    ret_str = ret_str.replace("%r", "?")
    # %s is sockets sent'd... can't currently get this via psutil
    ret_str = ret_str.replace("%s", "?")
    # %k is number of signals sent to this process... can't currently get this via psutil
    ret_str = ret_str.replace("%k", "?")
    ret_str = ret_str.replace("%C", f"{shlex.join(process_info.cmd)}")
    ret_str = ret_str.replace("%x", f"{process_info.exit_code}")

    # this is specifically last since it adds in a % sign
    try:
        ret_str = ret_str.replace(
            "%P",
            f"{process_info.get_percentage_of_cpu_this_job_got()}%",
        )
    except ZeroDivisionError:
        ret_str = ret_str.replace("%P", "0%")

    return ret_str


def main():
    parser = argparse.ArgumentParser(
        description="""A pseudo-port of GNU time to Python. You can look at the man page of time to get some info about the args here.
        Certain format codes are not supported and will return a ? in place of an actual value."""
    )
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="The command to time.")
    parser.add_argument("-p", dest="use_portable_format", action="store_true", help="Use the portable output format.")
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        default=None,
        help="Do not send the results to stderr, but overwrite the specified file.",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default=None,
        help="Specify output format, possibly overriding the format specified in the environment variable TIME.",
    )
    parser.add_argument(
        "-a", "--append", action="store_true", help="(Used together with -o.) Do not overwrite but append."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Give very verbose output about all the program knows about."
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Don't report abnormal program termination (where command is terminated by a signal) or nonzero exit status.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Print version information on standard output, then exit successfully.",
    )

    # this is a clocky extension to allow supporting a gnu-like mode
    parser.add_argument(
        "-g",
        dest="gnu_mode",
        action="store_true",
        help="A clocky-specific extension. When set, tries to act similar to gnu time in terms of output. Otherwise by default (without -f) clocky acts like bash's time command.",
    )

    args = parser.parse_args()

    if args.output is None:
        output = sys.stderr
    else:
        output = args.output.open("a+" if args.append else "w")

    try:
        if args.version:
            print(f"clocky {__version__}", end="", file=output)
        else:
            process_info = run(args.cmd, args.gnu_mode, quiet=args.quiet, output=output)

            if args.verbose:
                print(str(process_info), end="", file=output)
            elif args.use_portable_format:
                print(
                    f"real {process_info.run_time:.2f}\nuser {process_info.get_user_time():.2f}\nsys {process_info.get_sys_time():.2f}",
                    end="",
                    file=output,
                )
            elif args.gnu_mode:
                print(
                    process_custom_format_str(GNU_TIME_DEFAULT_FORMAT_STRING, process_info),
                    file=output,
                )
            elif args.format:
                print(process_custom_format_str(args.format, process_info), file=output)
            elif format := os.environ.get("TIME"):
                print(process_custom_format_str(format, process_info), file=output)
            else:
                print(
                    f"""
real    {seconds_to_time_str(process_info.run_time)}
user    {seconds_to_time_str(process_info.get_user_time())}
sys     {seconds_to_time_str(process_info.get_sys_time())}""",
                    end="",
                    file=output,
                )
    finally:
        if output != sys.stderr:
            output.close()


if __name__ == "__main__":
    main()
