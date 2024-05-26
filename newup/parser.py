import logging
import optparse
import shutil
import sys
import textwrap
from contextlib import suppress
from typing import Any, Dict, Generator, List, Tuple

from pip._internal.cli.status_codes import UNKNOWN_ERROR
from pip._internal.configuration import Configuration, ConfigurationError
from pip._internal.utils.misc import redact_auth_from_url, strtobool

logger = logging.getLogger(__name__)

class PrettyHelpFormatter(optparse.IndentedHelpFormatter):
    """A prettier/less verbose help formatter for optparse."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["max_help_position"] = 30
        kwargs["indent_increment"] = 1
        kwargs["width"] = shutil.get_terminal_size()[0] - 2
        super().__init__(*args, **kwargs)

    def format_option_strings(self, option: optparse.Option) -> str:
        return self._format_option_strings(option)

    def _format_option_strings(
        self, option: optparse.Option, mvarfmt: str = " <{}>", optsep: str = ", "
    ) -> str:
        opts = []
        if option._short_opts:
            opts.append(option._short_opts[0])
        if option._long_opts:
            opts.append(option._long_opts[0])
        if len(opts) > 1:
            opts.insert(1, optsep)
        if option.takes_value():
            assert option.dest is not None
            metavar = option.metavar or option.dest.lower()
            opts.append(mvarfmt.format(metavar.lower()))
        return "".join(opts)

    def format_heading(self, heading: str) -> str:
        if heading == "Options":
            return ""
        return heading + ":\n"

    def format_usage(self, usage: str) -> str:
        msg = "\nUsage: {}\n".format(self.indent_lines(textwrap.dedent(usage), "  "))
        return msg

    def format_description(self, description: str) -> str:
        if description:
            if hasattr(self.parser, "main"):
                label = "Commands"
            else:
                label = "Description"
            description = description.lstrip("\n").rstrip()
            description = self.indent_lines(textwrap.dedent(description), "  ")
            description = f"{label}:\n{description}\n"
            return description
        else:
            return ""

    def format_epilog(self, epilog: str) -> str:
        if epilog:
            return epilog
        else:
            return ""

    def indent_lines(self, text: str, indent: str) -> str:
        new_lines = [indent + line for line in text.split("\n")]
        return "\n".join(new_lines)


class UpdatingDefaultsHelpFormatter(PrettyHelpFormatter):
    """Custom help formatter for use in ConfigOptionParser."""

    def expand_default(self, option: optparse.Option) -> str:
        default_values = None
        if self.parser is not None:
            assert isinstance(self.parser, ConfigOptionParser)
            self.parser._update_defaults(self.parser.defaults)
            assert option.dest is not None
            default_values = self.parser.defaults.get(option.dest)
        help_text = super().expand_default(option)
        if default_values and option.metavar == "URL":
            if isinstance(default_values, str):
                default_values = [default_values]
            if not isinstance(default_values, list):
                default_values = []
            for val in default_values:
                help_text = help_text.replace(val, redact_auth_from_url(val))
        return help_text


class CustomOptionParser(optparse.OptionParser):
    def insert_option_group(
        self, idx: int, *args: Any, **kwargs: Any
    ) -> optparse.OptionGroup:
        group = self.add_option_group(*args, **kwargs)
        self.option_groups.pop()
        self.option_groups.insert(idx, group)
        return group

    @property
    def option_list_all(self) -> List[optparse.Option]:
        res = self.option_list[:]
        for i in self.option_groups:
            res.extend(i.option_list)
        return res


class ConfigOptionParser(CustomOptionParser):
    def __init__(
        self,
        *args: Any,
        name: str,
        isolated: bool = False,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.config = Configuration(isolated)
        assert self.name
        super().__init__(*args, **kwargs)

    def check_default(self, option: optparse.Option, key: str, val: Any) -> Any:
        try:
            return option.check_value(key, val)
        except optparse.OptionValueError as exc:
            print(f"An error occurred during configuration: {exc}")
            sys.exit(3)

    def _get_ordered_configuration_items(
        self,
    ) -> Generator[Tuple[str, Any], None, None]:
        override_order = ["global", self.name, ":env:"]
        section_items: Dict[str, List[Tuple[str, Any]]] = {
            name: [] for name in override_order
        }
        for section_key, val in self.config.items():
            if not val:
                logger.debug(
                    "Ignoring configuration key '%s' as it's value is empty.",
                    section_key,
                )
                continue
            section, key = section_key.split(".", 1)
            if section in override_order:
                section_items[section].append((key, val))
        for section in override_order:
            for key, val in section_items[section]:
                yield key, val

    def _update_defaults(self, defaults: Dict[str, Any]) -> Dict[str, Any]:
        self.values = optparse.Values(self.defaults)
        late_eval = set()
        for key, val in self._get_ordered_configuration_items():
            option = self.get_option("--" + key)
            if option is None:
                continue
            assert option.dest is not None
            if option.action in ("store_true", "store_false"):
                try:
                    val = strtobool(val)
                except ValueError:
                    self.error(
                        f"{val} is not a valid value for {key} option, "
                        "please specify a boolean value like yes/no, "
                        "true/false or 1/0 instead."
                    )
            elif option.action == "count":
                with suppress(ValueError):
                    val = strtobool(val)
                with suppress(ValueError):
                    val = int(val)
                if not isinstance(val, int) or val < 0:
                    self.error(
                        f"{val} is not a valid value for {key} option, "
                        "please instead specify either a non-negative integer "
                        "or a boolean value like yes/no or false/true "
                        "which is equivalent to 1/0."
                    )
            elif option.action == "append":
                val = val.split()
                val = [self.check_default(option, key, v) for v in val]
            elif option.action == "callback":
                assert option.callback is not None
                late_eval.add(option.dest)
                opt_str = option.get_opt_string()
                val = option.convert_value(opt_str, val)
                args = option.callback_args or ()
                kwargs = option.callback_kwargs or {}
                option.callback(option, opt_str, val, self, *args, **kwargs)
            else:
                val = self.check_default(option, key, val)
            defaults[option.dest] = val
        for key in late_eval:
            defaults[key] = getattr(self.values, key)
        self.values = None
        return defaults

    def get_default_values(self) -> optparse.Values:
        if not self.process_default_values:
            return optparse.Values(self.defaults)
        try:
            self.config.load()
        except ConfigurationError as err:
            self.exit(UNKNOWN_ERROR, str(err))
        defaults = self._update_defaults(self.defaults.copy())
        for option in self._get_all_options():
            assert option.dest is not None
            default = defaults.get(option.dest)
            if isinstance(default, str):
                opt_str = option.get_opt_string()
                defaults[option.dest] = option.check_value(opt_str, default)
        return optparse.Values(defaults)

    def error(self, msg: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(UNKNOWN_ERROR, f"{msg}\n")
