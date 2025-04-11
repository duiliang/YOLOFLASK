"""
逻辑规则服务模块
处理逻辑规则配置的保存、获取和删除
"""
import os
import json
from flask import current_app

def get_config():
    """
    获取全局配置
    
    Returns:
        dict: 配置信息
    """
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        current_app.logger.error(f"获取配置失败: {str(e)}")
        return {}

def save_config(config):
    """
    保存全局配置
    
    Args:
        config (dict): 配置信息
        
    Returns:
        bool: 是否保存成功
    """
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        current_app.logger.error(f"保存配置失败: {str(e)}")
        return False

def get_logic_rules():
    """
    获取所有逻辑规则配置
    
    Returns:
        dict: 所有逻辑规则配置
    """
    try:
        config = get_config()
        # 确保logic_rules字段存在
        if 'logic_rules' not in config:
            config['logic_rules'] = {}
            save_config(config)
        return config['logic_rules']
    except Exception as e:
        current_app.logger.error(f"获取逻辑规则配置失败: {str(e)}")
        return {}

def save_logic_rule(rule_name, roi_config, model, rules):
    """
    保存逻辑规则配置
    
    Args:
        rule_name (str): 规则配置名称
        roi_config (str): ROI配置名称
        model (str): 模型名称
        rules (list): 规则列表
        
    Returns:
        tuple: (是否成功, 消息)
    """
    try:
        config = get_config()
        
        # 确保logic_rules字段存在
        if 'logic_rules' not in config:
            config['logic_rules'] = {}
        
        # 保存规则配置
        config['logic_rules'][rule_name] = {
            'roi_config': roi_config,
            'model': model,
            'rules': rules
        }
        
        # 保存配置
        if save_config(config):
            return True, f"规则配置 '{rule_name}' 保存成功"
        else:
            return False, "保存配置文件失败"
    except Exception as e:
        current_app.logger.error(f"保存逻辑规则配置失败: {str(e)}")
        return False, f"保存失败: {str(e)}"

def delete_logic_rule(rule_name):
    """
    删除逻辑规则配置
    
    Args:
        rule_name (str): 规则配置名称
        
    Returns:
        tuple: (是否成功, 消息)
    """
    try:
        config = get_config()
        
        # 检查规则是否存在
        if 'logic_rules' not in config or rule_name not in config['logic_rules']:
            return False, f"规则配置 '{rule_name}' 不存在"
        
        # 删除规则
        del config['logic_rules'][rule_name]
        
        # 保存配置
        if save_config(config):
            return True, f"规则配置 '{rule_name}' 删除成功"
        else:
            return False, "保存配置文件失败"
    except Exception as e:
        current_app.logger.error(f"删除逻辑规则配置失败: {str(e)}")
        return False, f"删除失败: {str(e)}"

def validate_detection_results(detection_results, rule_name):
    """
    验证检测结果是否符合逻辑规则
    
    Args:
        detection_results (dict): 检测结果
        rule_name (str): 规则配置名称
        
    Returns:
        tuple: (是否通过, 消息)
    """
    try:
        # 获取规则配置
        rules = get_logic_rules().get(rule_name)
        if not rules:
            return True, f"未找到规则配置 '{rule_name}'"
        
        # 获取所有检测到的对象
        detections = detection_results.get('detections', [])
        
        # 按ROI区域和类别统计检测结果
        roi_class_counts = {}
        for detection in detections:
            roi_id = detection.get('roi_id')
            if roi_id is None:
                continue
                
            class_name = detection.get('class_name')
            if not class_name:
                continue
                
            if roi_id not in roi_class_counts:
                roi_class_counts[roi_id] = {}
                
            if class_name not in roi_class_counts[roi_id]:
                roi_class_counts[roi_id][class_name] = 0
                
            roi_class_counts[roi_id][class_name] += 1
        
        # 验证每条规则
        all_passed = True
        failed_rules = []
        
        for rule in rules.get('rules', []):
            roi_id = rule.get('roi_id')
            class_name = rule.get('class')
            operator = rule.get('operator')
            count = rule.get('count')
            
            # 获取实际数量
            actual_count = 0
            if roi_id in roi_class_counts and class_name in roi_class_counts[roi_id]:
                actual_count = roi_class_counts[roi_id][class_name]
            
            # 验证规则
            passed = False
            if operator == '==':
                passed = (actual_count == count)
            elif operator == '!=':
                passed = (actual_count != count)
            elif operator == '>':
                passed = (actual_count > count)
            elif operator == '<':
                passed = (actual_count < count)
            elif operator == '>=':
                passed = (actual_count >= count)
            elif operator == '<=':
                passed = (actual_count <= count)
            
            if not passed:
                all_passed = False
                failed_rules.append(f"ROI {roi_id + 1} {class_name} {operator} {count}，实际值: {actual_count}")
        
        if all_passed:
            return True, "所有规则验证通过"
        else:
            return False, f"验证失败: {', '.join(failed_rules)}"
    except Exception as e:
        current_app.logger.error(f"验证检测结果失败: {str(e)}")
        return False, f"验证失败: {str(e)}"
