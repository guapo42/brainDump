"""Sarah Chen — Senior Engineer / Co-worker. Peer collaboration and shared deliverables."""

from models.schemas import Platform
from simulation.agents.base import BaseAgent, SimMessage, SimState
from simulation.clock import SimWeek

PHOENIX = "Project Phoenix"
EPA = "EPA Data Modernization"


class SarahChenAgent(BaseAgent):

    def __init__(self):
        super().__init__("sarah")

    def generate_messages(self, week: SimWeek, state: SimState) -> list[SimMessage]:
        w = week.week_number
        msgs: list[SimMessage] = []

        # === Q1: Ramp-up and Phoenix data layer ===

        if w == 3:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Hey! Saw the Phoenix kickoff notes. I'll start on the data layer this week. "
                    "Can you share your initial schema thoughts by Friday? Want to make sure we're "
                    "aligned before I start building the migration scripts."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen", "schen@company.com")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Share initial Phoenix schema design with Sarah", assignee="You",
                                   due_date="2026-01-23", priority="medium", project=PHOENIX),
                    ],
                    summary="Sarah starting Phoenix data layer, needs schema alignment.",
                ),
            ))

        if w == 5:
            msgs.append(self._make_message(week,
                text=(
                    "Here's the draft data migration plan for Phoenix. I've mapped out the legacy "
                    "tables to the new schema. Let me know if the foreign key relationships look "
                    "right — I'm not sure about the audit_log table.\n\n"
                    "Also, I'll need the API contract from you before I can build the data access layer. "
                    "Can you have that ready by Feb 13?\n\nSarah"
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Review Sarah's Phoenix data migration plan", assignee="You",
                                   priority="high", project=PHOENIX),
                        self._task("Provide Phoenix API contract to Sarah", assignee="You",
                                   due_date="2026-02-13", priority="high", project=PHOENIX,),
                    ],
                    summary="Sarah shares Phoenix migration plan, needs API contract by Feb 13.",
                    tone=self._tone(urgency=0.5, deliverable=True, peer_progress=True),
                ),
            ))

        if w == 7:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Quick update — I finished the Phoenix data migration scripts. They're in PR #87. "
                    "Can you review when you get a chance? Not blocking yet but will be soon."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Review Sarah's Phoenix migration PR #87", assignee="You",
                                   priority="medium", project=PHOENIX),
                    ],
                    summary="Sarah's Phoenix migration scripts ready for review in PR #87.",
                ),
                resolves_tasks=["Handle Phoenix data layer"],
            ))

        # === Q2: Crunch — heavy collaboration ===

        if w == 10:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Hey, the migration scripts are passing on staging but I found a data truncation "
                    "issue with the legacy VARCHAR(50) fields. Some customer names are getting cut off. "
                    "I'll fix on my end but can you update the API validation to handle longer strings? "
                    "Needs to be done before milestone 1."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Update Phoenix API validation for longer string fields",
                                   assignee="You", due_date="2026-04-03", priority="high",
                                   project=PHOENIX),
                    ],
                    summary="Data truncation bug in migration. API validation update needed before M1.",
                ),
            ))

        if w == 11:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text="Fixed the truncation issue on my side. PR #102. Merging after CI passes.",
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    summary="Sarah fixed data truncation, PR #102 merging.",
                ),
            ))

        if w == 12:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "I'll handle the load testing for milestone 1 if you handle the API docs. "
                    "Deal? That way we can both finish by Friday."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Write Phoenix API documentation for milestone 1",
                                   assignee="You", due_date="2026-04-03", priority="high",
                                   project=PHOENIX),
                        self._task("Run Phoenix milestone 1 load testing", assignee="Sarah Chen",
                                   due_date="2026-04-03", priority="high", project=PHOENIX),
                    ],
                    summary="Sarah proposes splitting M1 work: she does load testing, you do API docs.",
                ),
            ))

        if w == 14:
            msgs.append(self._make_message(week,
                text=(
                    "Load testing results for Phoenix M1 are in. Good news: API throughput is solid "
                    "at 2400 req/s. Bad news: the batch endpoint degrades above 500 concurrent users. "
                    "I think we need connection pooling changes.\n\n"
                    "I've documented everything in Confluence. Can you look at the pooling config this "
                    "week? Marcus might be able to help profile it.\n\nSarah"
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen"), self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Fix Phoenix connection pooling for batch endpoint",
                                   assignee="You", priority="high", project=PHOENIX),
                    ],
                    summary="Phoenix load test: batch endpoint degrades at 500 users. Pooling fix needed.",
                    tone=self._tone(urgency=0.6, deliverable=True, peer_progress=True),
                ),
            ))

        # === Mid-year: shared deliverables ===

        if w == 19:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "My data layer work is done for M2. Handing off to Priya for the event pipeline. "
                    "I've documented the interfaces in the wiki. Let me know if Priya has questions — "
                    "happy to pair with her."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen"), self._person("Priya Patel")],
                    projects=[self._project(PHOENIX)],
                    summary="Sarah completes Phoenix data layer, hands off to Priya for event pipeline.",
                ),
                resolves_tasks=["Handle Phoenix data layer"],
            ))

        if w == 21:
            msgs.append(self._make_message(week,
                text=(
                    "Hey, I've been helping Priya debug the EPA ETL pipeline. The issue is in the "
                    "date parsing for the legacy data — they used like 4 different date formats. "
                    "I've written a normalizer utility. Can you review? PR #156.\n\n"
                    "Also, are you free Thursday for a brainstorm on the Phoenix caching strategy? "
                    "I think we should use Redis but want your input.\n\nSarah"
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen"), self._person("Priya Patel")],
                    projects=[self._project(PHOENIX), self._project(EPA)],
                    tasks=[
                        self._task("Review Sarah's date normalizer PR #156", assignee="You",
                                   priority="medium", project=EPA),
                        self._task("Attend Phoenix caching strategy brainstorm", assignee="You",
                                   priority="medium", project=PHOENIX),
                    ],
                    summary="Sarah helping with EPA date parsing. Wants Phoenix caching brainstorm.",
                ),
            ))

        # === Q3: UAT support + EPA wrap ===

        if w == 26:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Starting on the Phoenix UAT data seeding. I'll need the sanitized production "
                    "dataset from you — can you get that to me by July 3? I'll build the seeding "
                    "scripts around it."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Provide sanitized production dataset for Phoenix UAT",
                                   assignee="You", due_date="2026-07-03", priority="high",
                                   project=PHOENIX),
                    ],
                    summary="Sarah needs sanitized prod data for Phoenix UAT seeding by Jul 3.",
                    tone=self._tone(urgency=0.7, deliverable=True, peer_progress=True),
                ),
            ))

        if w == 29:
            msgs.append(self._make_message(week,
                text=(
                    "UAT data seeding is complete. Environment looks good. I ran a smoke test and "
                    "everything passes. The deployment runbook you sent is clear — I've signed off "
                    "on it.\n\nSarah"
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    summary="Sarah completes Phoenix UAT data seeding, signs off on runbook.",
                ),
                resolves_tasks=[
                    "Seed Phoenix UAT test data",
                    "Review Phoenix deployment runbook",
                ],
            ))

        if w == 34:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Phoenix go-live dry run went smooth. I'll be on standby this weekend for the "
                    "actual deployment. Ping me if anything comes up."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    summary="Sarah confirms Phoenix go-live dry run success, on standby.",
                ),
            ))

        # === Q4: Wind down ===

        if w == 38:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Post-launch monitoring looks stable. The rate-limit fix is holding. "
                    "I'm going to shift focus to some tech debt cleanup this month. "
                    "Want to pair on refactoring the data access layer? It's gotten messy."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Pair with Sarah on data access layer refactor",
                                   assignee="You", priority="low", project=PHOENIX),
                    ],
                    summary="Sarah proposes post-launch tech debt cleanup, pair refactoring.",
                ),
            ))

        if w == 42:
            msgs.append(self._make_message(week,
                text=(
                    "Hey, I'm putting together a knowledge transfer doc for Phoenix since the "
                    "project is entering maintenance mode. Can you review the architecture section "
                    "by October 23? I want to make sure it's accurate for whoever picks this up.\n\n"
                    "Sarah"
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Review Phoenix knowledge transfer doc", assignee="You",
                                   due_date="2026-10-23", priority="medium", project=PHOENIX),
                    ],
                    summary="Sarah writing Phoenix KT doc, architecture review needed by Oct 23.",
                ),
            ))

        if w == 50:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Thanks for a great year! Really enjoyed working together on Phoenix and "
                    "EPA. Let me know if you need anything for the year-end retro."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    summary="Sarah end-of-year thanks and retro availability.",
                ),
            ))

        # === Recurring: weekly coordination ===
        if w in (4, 6, 9, 15, 17, 20, 23, 25, 27, 31, 33, 36, 40, 44, 47):
            msgs.append(self._make_message(week, platform=Platform.SLACK, weekday=0, hour=9,
                text=(
                    f"Weekly sync — anything you need from me this week? I'm mostly heads-down "
                    f"on {'Phoenix data layer' if w < 20 else 'maintenance and cleanup'}."
                ),
                extraction=self._extraction(
                    people=[self._person("Sarah Chen")],
                    summary=f"Sarah's weekly sync check-in (W{w}).",
                ),
            ))

        return msgs
