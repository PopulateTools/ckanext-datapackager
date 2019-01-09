'''Functions for converting between CKAN's dataset and Data Packages.
'''
import re
import json

import six
import slugify
import ckan.plugins.toolkit as t

from ckan.common import config
from ckan_datapackage_tools import converter as original_converter

def default_locale():
    return config.get('ckan.locale_default')

def available_locales():
    return t.aslist(config.get('ckan.locales_offered', ['es', 'eu']))

def dataset_to_datapackage(dataset_dict):
    return original_converter.dataset_to_datapackage(dataset_dict)


def datapackage_to_dataset(datapackage):
    '''Convert the given datapackage into a CKAN dataset dict.

    :returns: the dataset dict
    :rtype: dict
    '''
    PARSERS = [
        _rename_dict_key('version', 'version'),
        _rename_dict_key('description', 'notes'),
        _datapackage_parse_i18n_title,
        _datapackage_parse_i18n_description,
        _datapackage_parse_license,
        _datapackage_parse_sources,
        _datapackage_parse_i18n_author,
        _datapackage_parse_i18n_maintainer,
        _parse_i18n_tags,
        _datapackage_parse_unknown_fields_as_extras
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

def _datapackage_parse_i18n_title(dataset_dict):
    return _parse_i18n_attr('title', dataset_dict)

def _datapackage_parse_i18n_description(dataset_dict):
    return _parse_i18n_attr('description', dataset_dict)

def _datapackage_parse_i18n_author(dataset_dict):
    return _parse_i18n_attr('author', dataset_dict)

def _datapackage_parse_i18n_maintainer(dataset_dict):
    return _parse_i18n_attr('maintainer', dataset_dict)

def _parse_i18n_tags(datapackage_dict):
    tags_vocabularies_ids = {}
    for locale in available_locales():
        tags_vocabularies_ids[locale] = t.get_action('vocabulary_show')(data_dict={'id': 'tags_' + locale})['id']

    result = { 'tags': [] }

    i18n_attribute = datapackage_dict.get('tags_translated')
    attribute = datapackage_dict.get('keywords')

    if len(i18n_attribute.keys()) > 0:
        for locale_key in i18n_attribute.keys():
            for tag in i18n_attribute[locale_key]:
                result['tags'].append({ 'name': unicode(tag), 'vocabulary_id': tags_vocabularies_ids[locale_key] })

    return result


def _parse_i18n_attr(attr_name, datapackage_dict):
    result = {}

    i18n_attr_name = attr_name + '_translated'
    attribute = datapackage_dict.get(attr_name)
    i18n_attribute = datapackage_dict.get(i18n_attr_name)

    if len(i18n_attribute.keys()) > 0:
        result[i18n_attr_name] = i18n_attribute
    elif attribute:
        result[i18n_attr_name] = {}
        for locale in available_locales():
            result[i18n_attr_name][locale] = attribute

    return result


def _datapackage_resource_to_ckan_resource(resource):
    resource_dict = {}

    if resource.descriptor.get('name'):
        name = resource.descriptor.get('title') or resource.descriptor['name']
        resource_dict['name'] = name

    if resource.descriptor.get('name_translated'):
        resource_dict['name_translated'] = resource.descriptor['name_translated']
    if resource.descriptor.get('description_translated'):
        resource_dict['description_translated'] = resource.descriptor['description_translated']

    if resource.local:
        resource_dict['path'] = resource.source
    elif resource.remote:
        resource_dict['url'] = resource.source
    elif resource.inline:
        resource_dict['data'] = resource.source
    else:
        raise NotImplementedError('Multipart resources not yet supported')

    if resource.descriptor.get('description'):
        resource_dict['description'] = resource.descriptor['description']

    if resource.descriptor.get('format'):
        resource_dict['format'] = resource.descriptor['format']

    if resource.descriptor.get('hash'):
        resource_dict['hash'] = resource.descriptor['hash']

    if resource.descriptor.get('schema'):
        resource_dict['schema'] = resource.descriptor['schema']

    return resource_dict


def _rename_dict_key(original_key, destination_key):
    return original_converter._rename_dict_key(original_key, destination_key)


def _parse_license(dataset_dict):
    return original_converter._parse_license(dataset_dict)


def _datapackage_parse_license(datapackage_dict):
    return original_converter._datapackage_parse_license(datapackage_dict)


def _datapackage_parse_sources(datapackage_dict):
    return original_converter._datapackage_parse_sources(datapackage_dict)


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
        'title_translated',
        'description',
        'description_translated',
        'homepage',
        'version',
        'sources',
        'author',
        'author_translated',
        'maintainer',
        'maintainer_translated',
        'tags_translated',
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
