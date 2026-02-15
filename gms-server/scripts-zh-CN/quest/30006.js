/*
每日任务：消灭污染怪物
任务ID: 30006
描述: 每日24:00刷新，击杀任意200个怪物，奖励2000点HP
*/

var status = -1; 

//Start
function start(mode, type, selection)
{
	if (CheckStatus(mode))
	{
	    if (status == 0)
	    {
			//第一层对话
			qm.sendAcceptDecline("黑魔法师的气息不断污染怪物，冒险者，请帮助我们消灭200只任意怪物");
	    }
		else if (status == 1)
		{
			if (mode == 0)
			{
				// 拒绝任务
				qm.sendOk("好吧，如果你改变主意了，随时可以来找我。");
				qm.dispose();
			}
			else
			{
				// 接受任务
				qm.forceStartQuest();
				qm.sendOk("太好了！请消灭任意200只怪物，完成后回来找我领取奖励。");
				qm.dispose();
			}
		}
	}
}

function end(mode, type, selection)
{
	if (CheckStatus(mode))
	{
	    if (status == 0)
	    {
			//第一层对话
			var player = qm.getPlayer();
			if (player != null) {
				player.addMaxHP(2000);
			}
            qm.sendOk("太好了！你成功消灭了200只怪物，这是给你的奖励：增加2000点HP上限！");		
			qm.forceCompleteQuest();
	    }
		else
		{
			//最后一层对话完继续循环至此，退出结束
			qm.dispose();
		}
	}
			
}

function CheckStatus(mode)
{
	if (mode == -1)
	{
		qm.dispose();
		return false;
	}
	
	if (mode == 1)
	{
		status++;
	}
	else
	{
		status--;
	}
	
	if (status == -1)
	{
		qm.dispose();
		return false;
	}	
	return true;
}
