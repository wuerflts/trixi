#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from vislogger.util import ModuleMultiTypeEncoder, ModuleMultiTypeDecoder


class Config(dict):

    def __init__(self, file_=None, config=None, update_from_argv=False, **kwargs):

        super(Config, self).__init__(**kwargs)
        self.__dict__ = self

        if file_ is not None:
            self.load(file_)

        if config is not None:
            self.update(config)

        self.update(kwargs)
        if update_from_argv:
            update_from_sys_argv(self)

    def dump(self, file_, indent=4, separators=(",", ": "), **kwargs):

        if hasattr(file_, "write"):
            json.dump(self, file_,
                      cls=ModuleMultiTypeEncoder,
                      indent=indent,
                      separators=separators,
                      **kwargs)
        else:
            with open(file_, "w") as file_object:
                json.dump(self, file_object,
                          cls=ModuleMultiTypeEncoder,
                          indent=indent,
                          separators=separators,
                          **kwargs)

    def load(self, file_, raise_=True, **kwargs):

        if hasattr(file_, "read"):
            new_dict = json.load(file_, cls=ModuleMultiTypeDecoder, **kwargs)
        else:
            with open(file_, "r") as file_object:
                new_dict = json.load(file_object, cls=ModuleMultiTypeDecoder, **kwargs)

        self.update(new_dict)


def update_from_sys_argv(config):

    import sys
    import argparse
    import warnings

    """Updates the current config with the arguments passed as args when running the programm and removes given
    classes / converts them to None"""

    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    def get_key_strings(config):
        """Converts hierarichal keys into a list of keys (depth first transversal)"""

        def parse_key_strings(config_dict, prefix_key=None):
            if prefix_key is None:
                prefix_key = []

            output_list = []
            for key in config_dict.keys():
                if isinstance(config_dict[key], dict):
                    sub_tree_list = parse_key_strings(config_dict[key], prefix_key=prefix_key + [key])
                    output_list += sub_tree_list
                else:
                    output_list.append(prefix_key + [key])
            return output_list

        keys = parse_key_strings(config)
        return keys

    def get_values_for_keys(config, key_list):
        """For a list of (hierarichal) keys return the corresponding value (--> tree search)"""
        output_val = config
        for key in key_list:
            output_val = output_val.get(key, {})
        return output_val

    def set_value_for_key(config, key_list, value):
        """For a list of (hierarichal) keys set a given value (--> tree search)"""
        assert len(key_list) > 0
        for key in key_list[:-1]:
            config = config[key]
        config[key_list[-1]] = value

    def update_keys(config, update_obj):
        for update_key, update_val in update_obj.items():
            keys = update_key.split(".")
            set_value_for_key(config, keys, update_val)

    if len(sys.argv) > 1:

        parser = argparse.ArgumentParser()

        # parse just config keys
        keys = get_key_strings(config)
        for key in keys:
            val = get_values_for_keys(config, key)
            param_name = ".".join(key)
            name_str = "--%s" % param_name
            if val is None:
                parser.add_argument(name_str)
            else:
                if type(val) == bool:
                    parser.add_argument(name_str, type=str2bool, default=val)
                else:
                    parser.add_argument(name_str, type=type(val), default=val)

        # parse args
        param, unknown = parser.parse_known_args()

        if len(unknown) > 0:
            warnings.warn("Called with unknown arguments: %s" % unknown, RuntimeWarning)

        # update dict
        update_keys(config, vars(param))
