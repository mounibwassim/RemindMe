from collections import Counter
from datetime import datetime, timedelta
from typing import List

from app.schemas import TaskResponse


class InsightsService:
    @staticmethod
    def generate_insights(tasks: List[TaskResponse]) -> str:
        if not tasks:
            return "🎯 **Fresh Start**\nCreate your first scheduled tasks to activate dynamic AI behavior tracking and weekly focus breakdowns."

        total = len(tasks)
        now = datetime.now()
        now_iso = now.isoformat()
        
        completed = [t for t in tasks if t.completed_iso]
        pending = [t for t in tasks if not t.completed_iso and t.due_iso <= now_iso]
        upcoming = [t for t in tasks if not t.completed_iso and t.due_iso > now_iso]
        overdue = [t for t in tasks if not t.completed_iso and t.is_overdue == 1]
        
        comp_rate = (len(completed) / total) * 100 if total > 0 else 0
        
        # Category analysis
        categories = [t.category for t in tasks if t.category]
        cat_counts = Counter(categories)
        top_cat = cat_counts.most_common(1)[0][0] if categories else "General"
        
        # Late categories (tasks that are overdue or were completed after deadline)
        # Note: TaskResponse doesn't explicitly have 'was_completed_late', but we can check if overdue=1
        overdue_cats = [t.category for t in overdue if t.category]
        bottleneck_cat = Counter(overdue_cats).most_common(1)[0][0] if overdue_cats else None

        insights = []
        
        # 1. Performance Insight
        if comp_rate >= 85:
            insights.append(f"🌟 **Elite Velocity**\nYou've completed **{comp_rate:.0f}%** of your scheduled tasks. Outstanding rhythm!")
        elif comp_rate >= 60:
            insights.append(f"📈 **Solid Progress**\nFinished **{comp_rate:.0f}%** of your tasks. Keep leveraging your focus to clear the remaining items.")
        else:
            insights.append(f"💡 **Opportunity Detected**\nCurrent completion is **{comp_rate:.0f}%**. Focus on your **{len(overdue)} overdue** items to regain your peak momentum.")

        # 2. Behavioral Trend
        if bottleneck_cat:
            insights.append(f"🐢 **Category Bottleneck**\nNoticeable delays detected in **{bottleneck_cat}** tasks. Consider scheduling these for earlier in your day.")
        elif top_cat:
            insights.append(f"📊 **Focus Alignment**\nYour primary focus area is **{top_cat}**. You are effectively prioritizing activities in this domain.")

        # 3. Time Management
        if not overdue and total > 0:
            insights.append(f"🚀 **Schedule Mastery**\nZero overdue tasks! Your time management has reached an elite level this week.")
        elif len(overdue) > 3:
            insights.append(f"⚠️ **Attention Required**\nMultiple deadlines missed (**{len(overdue)}**). Your current workload might be over-leveraged; try snoozing non-essential items.")

        return "\n\n".join(insights)
