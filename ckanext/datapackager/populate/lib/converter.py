'''Functions for converting between CKAN's dataset and Data Packages.
'''
import re
import json

import six
import slugify
import ckan.plugins.toolkit as t

from ckan_datapackage_tools import converter as original_converter

def _convert_to_datapackage_resource(resource_dict):
    return original_converter._convert_to_datapackage_resource(dataset_dict)


def dataset_to_datapackage(dataset_dict):
    return original_converter.dataset_to_datapackage(dataset_dict)


def datapackage_to_dataset(datapackage):
    '''Convert the given datapackage into a CKAN dataset dict.

    :returns: the dataset dict
    :rtype: dict
    '''
    PARSERS = [
        _rename_dict_key('title', 'title'),
        _rename_dict_key('version', 'version'),
        _rename_dict_key('description', 'notes'),
        _datapackage_parse_license,
        _datapackage_parse_sources,
        _datapackage_parse_author,
        _datapackage_parse_keywords,
        _datapackage_parse_unknown_fields_as_extras,
    ]

    dataset_dict = {
        'name': datapackage.descriptor['name'].lower(),
        'owner_org': datapackage.descriptor['owner_org'].lower(),
        'private': t.asbool(datapackage.descriptor['private'])
    }

    for parser in PARSERS:
        dataset_dict.update(parser(datapackage.descriptor))

    if datapackage.resources:
        dataset_dict['resources'] = [_datapackage_resource_to_ckan_resource(r)
                                     for r in datapackage.resources]

    return dataset_dict


def _datapackage_resource_to_ckan_resource(resource):
    return original_converter._datapackage_resource_to_ckan_resource(resource)


def _rename_dict_key(original_key, destination_key):
    return original_converter._rename_dict_key(original_key, destination_key)

def _parse_ckan_url(dataset_dict):
    return original_converter._parse_ckan_url(dataset_dict)


def _parse_notes(dataset_dict):
    return original_converter._parse_notes(dataset_dict)


def _parse_license(dataset_dict):
    return original_converter._parse_license(dataset_dict)


def _parse_author_and_source(dataset_dict):
    return original_converter._parse_author_and_source(dataset_dict)


def _parse_maintainer(dataset_dict):
    return original_converter._parse_maintainer(dataset_dict)


def _parse_tags(dataset_dict):
    return original_converter._parse_tags(dataset_dict)


def _parse_extras(dataset_dict):
    return original_converter._parse_extras(dataset_dict)


def _datapackage_parse_license(datapackage_dict):
    return original_converter._datapackage_parse_license(datapackage_dict)


def _datapackage_parse_sources(datapackage_dict):
    return original_converter._datapackage_parse_sources(datapackage_dict)


def _datapackage_parse_author(datapackage_dict):
    return original_converter._datapackage_parse_author(datapackage_dict)


def _datapackage_parse_keywords(datapackage_dict):
    return original_converter._datapackage_parse_keywords(datapackage_dict)


def _datapackage_parse_unknown_fields_as_extras(datapackage_dict):
    # FIXME: It's bad to hardcode it here. Instead, we should change the
    # parsers pattern to remove whatever they use from the `datapackage_dict`
    # and call this parser at last. Anything that's still in `datapackage_dict`
    # would then be added to extras.
    KNOWN_FIELDS = [
        'name',
        'resources',
        'license',
        'title',
        'description',
        'homepage',
        'version',
        'sources',
        'author',
        'keywords',
        'owner_org',
        'private'
    ]

    result = {}
    extras = [{'key': k, 'value': v}
              for k, v in datapackage_dict.items()
              if k not in KNOWN_FIELDS]

    if extras:
        for extra in extras:
            value = extra['value']
            if isinstance(value, dict) or isinstance(value, list):
                extra['value'] = json.dumps(value)
        result['extras'] = extras

    return result
