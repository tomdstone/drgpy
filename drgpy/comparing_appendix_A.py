"""
DRG Appendix A Comparison Tool

This script compares DRG definitions between two versions of the MS-DRG system
by analyzing appendix_A.txt files using the core DRG grouper's parsing logic.

The comparison includes:
1. Basic DRG information:
   - DRG code
   - MDC (Major Diagnostic Category)
   - Type (Medical/Surgical)
   - Description

2. Types of changes detected:
   - New DRGs
   - Removed DRGs
   - MDC changes
   - Type changes
   - Description changes
   - Unchanged DRGs

Usage:
    # Show just summary counts
    python -m drgpy.comparing_appendix_A v41 v42 --summary

    # Show summary and 5 examples for each change type
    python -m drgpy.comparing_appendix_A v41 v42 --examples 5

    # Show summary and 10 examples for each change type
    python -m drgpy.comparing_appendix_A v41 v42 --examples 10
"""

import os
import argparse
import difflib
from drgpy._appndxrdr import read_a


def get_available_versions():
    """Get list of available versions in data directory"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    return [d for d in os.listdir(data_dir) 
            if os.path.isdir(os.path.join(data_dir, d)) and d.startswith('v')]


def validate_versions(v1, v2):
    """Validate that versions exist and are different"""
    available = get_available_versions()
    msg = "Version {} not found. Available versions: {}"
    if v1 not in available:
        raise ValueError(msg.format(v1, available))
    if v2 not in available:
        raise ValueError(msg.format(v2, available))
    if v1 == v2:
        raise ValueError("Please specify different versions for comparison")
    return True


def read_appendix_a(version):
    """Read appendix A using _appndxrdr's read_a function"""
    return read_a(f"data/{version}/appendix_A.txt")


def compare_drg_info(v1_info, v2_info):
    """Compare DRG information between versions"""
    all_drgs = sorted(set(v1_info.keys()) | set(v2_info.keys()))
    
    changes = {
        'new': [],           # New DRGs in v2
        'removed': [],       # DRGs removed in v2
        'mdc_changed': [],   # MDC assignment changes
        'type_changed': [],  # Medical/Surgical changes
        'desc_changed': [],  # Description changes
        'unchanged': []      # No changes
    }
    
    for drg in all_drgs:
        if drg not in v1_info:
            changes['new'].append((drg, v2_info[drg]))
        elif drg not in v2_info:
            changes['removed'].append((drg, v1_info[drg]))
        else:
            v1_data = v1_info[drg]
            v2_data = v2_info[drg]
            
            if v1_data['mdc'] != v2_data['mdc']:
                changes['mdc_changed'].append((drg, v1_data, v2_data))
            # Check medical/surgical type changes
            elif ((v1_data['is_medical'], v1_data['is_surgical']) != 
                  (v2_data['is_medical'], v2_data['is_surgical'])):
                changes['type_changed'].append((drg, v1_data, v2_data))
            elif v1_data['desc'] != v2_data['desc']:
                changes['desc_changed'].append((drg, v1_data, v2_data))
            else:
                changes['unchanged'].append(drg)
    
    return changes


def highlight_changes(old_text, new_text):
    """Highlight the differences between two texts"""
    differ = difflib.SequenceMatcher(None, old_text, new_text)
    
    old_highlighted = []
    new_highlighted = []
    
    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'equal':
            old_highlighted.append(old_text[i1:i2])
            new_highlighted.append(new_text[j1:j2])
        elif tag == 'delete':
            old_highlighted.append(f"\033[91m{old_text[i1:i2]}\033[0m")
        elif tag == 'insert':
            new_highlighted.append(f"\033[92m{new_text[j1:j2]}\033[0m")
        elif tag == 'replace':
            old_highlighted.append(f"\033[91m{old_text[i1:i2]}\033[0m")
            new_highlighted.append(f"\033[92m{new_text[j1:j2]}\033[0m")
    
    return ''.join(old_highlighted), ''.join(new_highlighted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compare DRG definitions between versions')
    parser.add_argument('version1', help='First version (e.g., v40)')
    parser.add_argument('version2', help='Second version (e.g., v41)')
    parser.add_argument('--summary', action='store_true',
                       help='Show only summary counts of changes')
    parser.add_argument('--examples', type=int, metavar='N',
                       help='Show N examples for each change type')
    
    args = parser.parse_args()
    
    try:
        validate_versions(args.version1, args.version2)
        
        print(f"\n=== Comparing DRG info between {args.version1} "
              f"and {args.version2} ===\n")
        
        v1_info = read_appendix_a(args.version1)
        v2_info = read_appendix_a(args.version2)
        changes = compare_drg_info(v1_info, v2_info)
        
        # Print summary counts
        print("Summary of changes:")
        print(f"  Total DRGs in {args.version1}: {len(v1_info)}")
        print(f"  Total DRGs in {args.version2}: {len(v2_info)}")
        print(f"  New DRGs: {len(changes['new'])}")
        print(f"  Removed DRGs: {len(changes['removed'])}")
        print(f"  MDC changes: {len(changes['mdc_changed'])}")
        print(f"  Type changes (Surgical/Medical): {len(changes['type_changed'])}")
        print(f"  Description changes: {len(changes['desc_changed'])}")
        print(f"  Unchanged DRGs: {len(changes['unchanged'])}")
        
        # Show examples if requested
        if args.examples:
            N = args.examples
            
            if changes['new']:
                print(f"\nNew DRGs (showing {min(N, len(changes['new']))} of {len(changes['new'])}):")
                for drg, info in changes['new'][:N]:
                    print(f"  DRG {drg}: MDC={info['mdc']}, "
                          f"Type={'Medical' if info['is_medical'] else 'Surgical' if info['is_surgical'] else 'Other'}, "
                          f"Desc={info['desc']}")
            
            if changes['removed']:
                print(f"\nRemoved DRGs (showing {min(N, len(changes['removed']))} of {len(changes['removed'])}):")
                for drg, info in changes['removed'][:N]:
                    print(f"  DRG {drg}: MDC={info['mdc']}, "
                          f"Type={'Medical' if info['is_medical'] else 'Surgical' if info['is_surgical'] else 'Other'}, "
                          f"Desc={info['desc']}")
            
            if changes['mdc_changed']:
                print(f"\nMDC Changes (showing {min(N, len(changes['mdc_changed']))} of {len(changes['mdc_changed'])}):")
                for drg, v1, v2 in changes['mdc_changed'][:N]:
                    print(f"  DRG {drg}:")
                    print(f"    {args.version1}: MDC={v1['mdc']}")
                    print(f"    {args.version2}: MDC={v2['mdc']}")
            
            if changes['type_changed']:
                print(f"\nType Changes (showing {min(N, len(changes['type_changed']))} of {len(changes['type_changed'])}):")
                for drg, v1, v2 in changes['type_changed'][:N]:
                    print(f"  DRG {drg}:")
                    v1_type = 'Medical' if v1['is_medical'] else 'Surgical' if v1['is_surgical'] else 'Other'
                    v2_type = 'Medical' if v2['is_medical'] else 'Surgical' if v2['is_surgical'] else 'Other'
                    print(f"    {args.version1}: Type={v1_type}")
                    print(f"    {args.version2}: Type={v2_type}")
            
            if changes['desc_changed']:
                print(f"\nDescription Changes (showing {min(N, len(changes['desc_changed']))} of {len(changes['desc_changed'])}):")
                for drg, v1, v2 in changes['desc_changed'][:N]:
                    old_desc, new_desc = highlight_changes(v1['desc'], v2['desc'])
                    print(f"  DRG {drg}:")
                    print(f"    {args.version1}: {old_desc}")
                    print(f"    {args.version2}: {new_desc}")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"\nAvailable versions: {get_available_versions()}") 