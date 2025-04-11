"""
逻辑规则控制器模块
处理与逻辑规则相关的路由请求
"""
from flask import request, jsonify, current_app
from app.services.logic_service import get_logic_rules, save_logic_rule, delete_logic_rule

def handle_get_logic_rules():
    """
    处理获取所有逻辑规则配置的请求
    
    Returns:
        JSON响应: 所有逻辑规则配置
    """
    try:
        logic_rules = get_logic_rules()
        return jsonify({
            'success': True,
            'data': logic_rules
        })
    except Exception as e:
        current_app.logger.error(f"获取逻辑规则配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取逻辑规则配置失败: {str(e)}"
        }), 500

def handle_save_logic_rule():
    """
    处理保存逻辑规则配置的请求
    
    Returns:
        JSON响应: 保存结果
    """
    try:
        # 获取请求数据
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': "请求数据无效"
            }), 400
            
        # 获取参数
        rule_name = data.get('rule_name')
        roi_config = data.get('roi_config')
        model = data.get('model')
        rules = data.get('rules', [])
        
        # 验证参数
        if not rule_name:
            return jsonify({
                'success': False,
                'message': "规则配置名称不能为空"
            }), 400
            
        if not roi_config:
            return jsonify({
                'success': False,
                'message': "ROI配置名称不能为空"
            }), 400
            
        if not model:
            return jsonify({
                'success': False,
                'message': "模型名称不能为空"
            }), 400
            
        if not rules:
            return jsonify({
                'success': False,
                'message': "规则列表不能为空"
            }), 400
            
        # 保存规则配置
        success, message = save_logic_rule(rule_name, roi_config, model, rules)
        
        # 返回结果
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500
    except Exception as e:
        current_app.logger.error(f"保存逻辑规则配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"保存逻辑规则配置失败: {str(e)}"
        }), 500

def handle_delete_logic_rule():
    """
    处理删除逻辑规则配置的请求
    
    Returns:
        JSON响应: 删除结果
    """
    try:
        # 获取规则名称
        rule_name = request.args.get('rule_name')
        if not rule_name:
            return jsonify({
                'success': False,
                'message': "规则配置名称不能为空"
            }), 400
            
        # 删除规则配置
        success, message = delete_logic_rule(rule_name)
        
        # 返回结果
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 404 if "不存在" in message else 500
    except Exception as e:
        current_app.logger.error(f"删除逻辑规则配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"删除逻辑规则配置失败: {str(e)}"
        }), 500
