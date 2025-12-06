/*
脚本：领取技能
作者：flona
日期：2025-10-24
备注：玩家可选择领取轻舞飞扬或瞬间移动技能,每个角色限领一次
 */

var status;
var selectedSkill = -1;

// 技能配置
var SKILL_LIGHT_DANCE = 11111004;  // 轻舞飞扬
var TWO_JUMP = 4111006;      // 二段跳
var BIG_FEIBIAO = 4111005; // 二段跳前置大标要5级

function start() {
    status = -1;
    action(1, 0, 0);
}

function action(mode, type, selection) {
    if (CheckStatus(mode)) {
        if (status == 0) {
            // 第一层对话 - 检查是否已领取
            var strGetText = cm.getCharacterExtendValue("领取技能");
            if (strGetText == "已领取") {
                cm.sendOk("您已经领取过技能了。每个角色#r限领一次。#k");
                cm.dispose();
            } else {
                cm.sendSimple("请选择你想要领取的技能:\r\n#b" +
                    "#L0#轻舞飞扬 (剑客技能)#l\r\n" +
                    "#L1#二段跳#l");
            }
        } else if (status == 1) {
            // 第二层对话 - 确认选择
            selectedSkill = selection == 0 ? SKILL_LIGHT_DANCE : TWO_JUMP;
            var skillName = selection == 0 ? "轻舞飞扬" : "二段跳";

            cm.sendAcceptDecline("确定要领取 #b" + skillName + "#k 技能吗?\r\n" +
                "注意:每个角色#r限领一次#k,请慎重选择!");
        } else if (status == 2) {
            // 第三层对话 - 发放技能
            if(selectedSkill === TWO_JUMP){
                cm.teachSkill(TWO_JUMP, 20, 0, -1);
                cm.teachSkill(BIG_FEIBIAO, 5, 0, -1);
            }
            else{
                cm.teachSkill(selectedSkill, 1, 30, -1);
            }
            cm.saveOrUpdateCharacterExtendValue("领取技能", "已领取");

            cm.sendOk("恭喜您成功领取技能,祝您游戏愉快!");
            cm.dispose();
        } else {
            cm.dispose();
        }
    }
}

function CheckStatus(mode) {
    if (mode == -1) {
        cm.dispose();
        return false;
    }

    if (mode == 1) {
        status++;
    } else {
        status--;
    }

    if (status == -1) {
        cm.dispose();
        return false;
    }
    return true;
}