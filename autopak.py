import json
import os
import shutil
import sys
from collections import namedtuple
from hashlib import md5
from zipfile import ZipFile

MOD_DEFINITION_PATH = 'mods.json'
DEPLOY_TARGET = 'target'

Mod = namedtuple('Mod', [
    'game_title',
    'mod_title',
    'is_pk4',
    'sources',
    'base_path',
    'game',
    'zip_name',
    'pk4_name',
    'should_deploy'
])

def get_source_paths(source):
    return [os.path.join(r, f) for r,d,fs in os.walk(source) for f in fs]

def mod_definition_decoder(obj):
    return Mod(
        game_title=obj['game_title'],
        mod_title=obj['mod_title'],
        is_pk4=obj['is_pk4'],
        sources=obj['sources'],
        base_path=obj['base_path'],
        game=obj['game'],
        zip_name=obj['zip_name'],
        pk4_name=obj['pk4_name'],
        should_deploy=obj['should_deploy']
    )

def zip_sources(source_data, zip_dir_path, zip_name, zip_type, container_dir=None):
    if not os.path.exists(zip_dir_path):
        os.makedirs(zip_dir_path)
    zip_path = os.path.join(zip_dir_path, zip_name + '.' + zip_type)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    z = ZipFile(zip_path, 'w')
    for source, source_paths in source_data:
        zip_paths = [
            (x, os.path.relpath(x, source))
            for x in source_paths
        ] if not container_dir else [
            (x, os.path.join(container_dir, os.path.relpath(x, source)))
            for x in source_paths
        ]
        for src, arc in zip_paths:
            try:
                z.write(src, arcname=arc)
            except UserWarning:
                pass

def copy_sources(source_data, copy_dir_path):
    for source, source_paths in source_data:
            copy_paths = [
                (x, os.path.join(copy_dir_path, os.path.relpath(x, source)))
                for x in source_paths
            ]
            for src, dst in copy_paths:
                dst_parent = os.path.dirname(dst)
                if not os.path.exists(dst_parent):
                    os.makedirs(dst_parent)
                elif os.path.isfile(dst):
                    with open(src, 'rb') as f_src, open(dst, 'rb') as f_dst:
                        left = md5(f_src.read()).hexdigest()
                        right = md5(f_dst.read()).hexdigest()
                        if left == right:
                            continue
                        os.remove(dst)
                shutil.copy(src, dst)

def main():
    args = sys.argv
    goal = args[1]
    mod_defs = json.loads(open(MOD_DEFINITION_PATH, 'r').read(),
        object_hook=mod_definition_decoder)
    for mod in mod_defs:
        source_data = [
            (source, get_source_paths(source))
            for source in mod.sources
        ]
        if goal == 'install':
            print('Installing', mod.mod_title, 'for', mod.game_title, 'to', os.path.join(mod.base_path, mod.game, mod.pk4_name + '.pk4' if mod.is_pk4 and mod.pk4_name else ''))
            if mod.is_pk4:
                zip_sources(source_data, os.path.join(mod.base_path, mod.game), 
                    mod.pk4_name, 'pk4')
            else:
                copy_sources(source_data, os.path.join(mod.base_path, mod.game))
        elif goal == 'deploy' and mod.should_deploy:
            print('Deploying', mod.mod_title, 'for', mod.game_title)
            if mod.is_pk4:
                zip_sources(source_data, DEPLOY_TARGET, mod.pk4_name, 'pk4')
            else:
                zip_sources(source_data, DEPLOY_TARGET, mod.zip_name, 'zip',
                    container_dir=mod.game)
        else:
            pass

if __name__ == '__main__':
    main()