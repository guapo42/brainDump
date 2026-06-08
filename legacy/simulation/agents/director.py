"""Robert Kim — Project Director. Manages Phoenix and EPA project timelines."""

from models.schemas import Platform
from simulation.agents.base import BaseAgent, SimMessage, SimState
from simulation.clock import SimWeek

PHOENIX = "Project Phoenix"
EPA = "EPA Data Modernization"


class RobertKimAgent(BaseAgent):

    def __init__(self):
        super().__init__("robert")

    def generate_messages(self, week: SimWeek, state: SimState) -> list[SimMessage]:
        w = week.week_number
        msgs: list[SimMessage] = []

        # ===== PROJECT PHOENIX STORYLINE =====

        # W3: Kickoff
        if w == 3:
            msgs.append(self._make_message(week,
                text=(
                    "Team,\n\nProject Phoenix is officially kicking off. I've attached the charter and "
                    "initial scope document. Key milestones:\n"
                    "- Design review: Feb 13\n- Milestone 1 (API layer): April 3\n"
                    "- Milestone 2 (Integration): June 12\n- UAT: Aug 28\n- Go-live: Sep 4\n\n"
                    "I need you to own the backend architecture. Sarah will handle the data layer. "
                    "Please have a technical design doc ready for review by Feb 6.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[
                        self._person("Robert Kim", "rkim@company.com", "Project Director"),
                        self._person("Sarah Chen"),
                        self._person("You"),
                    ],
                    projects=[self._project(PHOENIX, priority="critical")],
                    tasks=[
                        self._task("Write Phoenix technical design doc", assignee="You",
                                   due_date="2026-02-06", priority="high", project=PHOENIX),
                        self._task("Own Phoenix backend architecture", assignee="You",
                                   project=PHOENIX, priority="high"),
                        self._task("Handle Phoenix data layer", assignee="Sarah Chen",
                                   project=PHOENIX, priority="high"),
                    ],
                    summary="Project Phoenix kickoff. Design doc due Feb 6, key milestones through Sep.",
                ),
            ))

        # W6: Design review
        if w == 6:
            msgs.append(self._make_message(week,
                text=(
                    "Design review for Phoenix is this Friday. I need the following from you before "
                    "the meeting:\n1. Finalized architecture diagram\n2. API contract draft\n"
                    "3. Risk register with your top 3 concerns\n\nSend these by Thursday EOD.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Finalize Phoenix architecture diagram", assignee="You",
                                   due_date="2026-02-12", priority="high", project=PHOENIX),
                        self._task("Draft Phoenix API contract", assignee="You",
                                   due_date="2026-02-12", priority="high", project=PHOENIX),
                        self._task("Prepare Phoenix risk register", assignee="You",
                                   due_date="2026-02-12", priority="medium", project=PHOENIX),
                    ],
                    summary="Phoenix design review Friday. Architecture, API contract, risk register needed.",
                ),
            ))

        # W10: Status check
        if w == 10:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "Quick check — how's the Phoenix API layer coming? We're 3 weeks out from "
                    "milestone 1. Any blockers I should raise with stakeholders?"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Provide Phoenix milestone 1 status update", assignee="You",
                                   priority="high", project=PHOENIX),
                    ],
                    summary="Robert checking Phoenix API progress, 3 weeks to milestone 1.",
                ),
            ))

        # W13: Milestone 1 crunch
        if w == 13:
            msgs.append(self._make_message(week,
                text=(
                    "URGENT: Milestone 1 for Phoenix (API layer) is due this Friday April 3rd. "
                    "I need a go/no-go assessment from you by Wednesday. If we're at risk, I need "
                    "to know NOW so I can negotiate with the client.\n\nAlso, what's Marcus's status "
                    "on the unit tests? He should be done by now.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim"), self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX, priority="critical")],
                    tasks=[
                        self._task("Submit Phoenix milestone 1 go/no-go assessment", assignee="You",
                                   due_date="2026-04-01", priority="critical", project=PHOENIX),
                        self._task("Complete Phoenix API unit tests", assignee="Marcus Webb",
                                   due_date="2026-04-03", priority="high", project=PHOENIX,
                                   waiting_on="You"),
                    ],
                    summary="URGENT: Phoenix milestone 1 due Friday. Go/no-go needed Wednesday.",
                    tone=self._tone(urgency=1.0, temperature="panicked",
                                    deliverable=True, peer_progress=True),
                ),
            ))

        # W16: Post-milestone retrospective
        if w == 16:
            msgs.append(self._make_message(week,
                text=(
                    "Good work pushing milestone 1 through. A few things for the retro:\n"
                    "- The API contract changes mid-sprint cost us 3 days. Let's lock specs earlier.\n"
                    "- Marcus flagged that he waited 5 days for your code review. We need to tighten "
                    "the review cycle.\n\nPlease document lessons learned by April 24.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim"), self._person("Marcus Webb")],
                    projects=[self._project(PHOENIX)],
                    tasks=[
                        self._task("Document Phoenix milestone 1 lessons learned", assignee="You",
                                   due_date="2026-04-24", priority="medium", project=PHOENIX),
                    ],
                    summary="Phoenix M1 retro. Code review delays flagged, lessons learned due Apr 24.",
                    tone=self._tone(urgency=0.3, temperature="frustrated", follow_up=True),
                ),
                resolves_tasks=["Submit Phoenix milestone 1 go/no-go assessment"],
            ))

        # W20: Milestone 2 planning
        if w == 20:
            msgs.append(self._make_message(week,
                text=(
                    "Milestone 2 (Integration) is June 12. Here's what I need:\n"
                    "- You: Complete the service mesh integration and write the deployment runbook\n"
                    "- Priya: Finish the event pipeline and hook it into the Phoenix backend\n"
                    "- Marcus: Integration test suite\n\n"
                    "Sarah's data layer work feeds into Priya's pipeline. Make sure that handoff "
                    "happens cleanly by May 22.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[
                        self._person("Robert Kim"),
                        self._person("Priya Patel"),
                        self._person("Marcus Webb"),
                        self._person("Sarah Chen"),
                    ],
                    projects=[self._project(PHOENIX, priority="critical")],
                    tasks=[
                        self._task("Complete Phoenix service mesh integration", assignee="You",
                                   due_date="2026-06-12", priority="high", project=PHOENIX),
                        self._task("Write Phoenix deployment runbook", assignee="You",
                                   due_date="2026-06-12", priority="medium", project=PHOENIX),
                        self._task("Finish Phoenix event pipeline", assignee="Priya Patel",
                                   due_date="2026-06-12", priority="high", project=PHOENIX,
                                   waiting_on="Sarah Chen"),
                        self._task("Write Phoenix integration test suite", assignee="Marcus Webb",
                                   due_date="2026-06-12", priority="high", project=PHOENIX,
                                   waiting_on="You"),
                    ],
                    summary="Phoenix M2 planning. Integration due June 12, multiple dependencies.",
                ),
            ))

        # W24: Milestone 2 crunch
        if w == 24:
            msgs.append(self._make_message(week,
                text=(
                    "We're 2 weeks out from milestone 2. Status report needed by Monday.\n\n"
                    "I know EPA is also heating up but Phoenix has client visibility. If you need "
                    "to deprioritize something, talk to me first.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim")],
                    projects=[self._project(PHOENIX, priority="critical"), self._project(EPA)],
                    tasks=[
                        self._task("Submit Phoenix milestone 2 status report", assignee="You",
                                   due_date="2026-06-15", priority="critical", project=PHOENIX),
                    ],
                    summary="Phoenix M2 crunch. Status report needed. Warns about EPA competing priority.",
                    tone=self._tone(urgency=0.9, escalation=True, temperature="frustrated",
                                    deliverable=True),
                ),
            ))

        # W28: UAT prep
        if w == 28:
            msgs.append(self._make_message(week,
                text=(
                    "Phoenix UAT starts August 28. I need the following ready by August 21:\n"
                    "1. UAT environment provisioned and stable\n"
                    "2. Test data seeded\n"
                    "3. Runbook reviewed by Sarah\n\n"
                    "This is the last gate before go-live. No surprises.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim"), self._person("Sarah Chen")],
                    projects=[self._project(PHOENIX, priority="critical")],
                    tasks=[
                        self._task("Provision Phoenix UAT environment", assignee="You",
                                   due_date="2026-08-21", priority="critical", project=PHOENIX),
                        self._task("Seed Phoenix UAT test data", assignee="You",
                                   due_date="2026-08-21", priority="high", project=PHOENIX),
                        self._task("Review Phoenix deployment runbook", assignee="Sarah Chen",
                                   due_date="2026-08-21", priority="high", project=PHOENIX,
                                   waiting_on="You"),
                    ],
                    summary="Phoenix UAT prep. Environment, test data, runbook review due Aug 21.",
                ),
            ))

        # W35: Go-live week
        if w == 35:
            msgs.append(self._make_message(week,
                text=(
                    "Phoenix go-live is next Friday September 4th. Final checklist:\n"
                    "- Deployment runbook signed off?\n- Rollback plan documented?\n"
                    "- On-call schedule confirmed for launch weekend?\n\n"
                    "Please confirm all green by Wednesday.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim")],
                    projects=[self._project(PHOENIX, priority="critical")],
                    tasks=[
                        self._task("Confirm Phoenix go-live readiness", assignee="You",
                                   due_date="2026-09-02", priority="critical", project=PHOENIX),
                        self._task("Document Phoenix rollback plan", assignee="You",
                                   due_date="2026-09-02", priority="critical", project=PHOENIX),
                    ],
                    summary="Phoenix go-live Sep 4. Final checklist and readiness confirmation needed.",
                    tone=self._tone(urgency=1.0, escalation=True, temperature="panicked",
                                    deliverable=True),
                ),
            ))

        # W37: Post-launch
        if w == 37:
            msgs.append(self._make_message(week,
                text=(
                    "Phoenix is live! Great work team. A few post-launch items:\n"
                    "- We hit a rate-limiting issue on day 2. Please write a post-mortem by Sep 18.\n"
                    "- The client wants a 30-day stability report. Let's track metrics starting now.\n\n"
                    "Robert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim")],
                    projects=[self._project(PHOENIX, status="active")],
                    tasks=[
                        self._task("Write Phoenix launch post-mortem", assignee="You",
                                   due_date="2026-09-18", priority="high", project=PHOENIX),
                        self._task("Track Phoenix 30-day stability metrics", assignee="You",
                                   due_date="2026-10-04", priority="medium", project=PHOENIX),
                    ],
                    summary="Phoenix live. Post-mortem needed for rate-limit issue, 30-day stability tracking.",
                ),
                resolves_tasks=[
                    "Confirm Phoenix go-live readiness",
                    "Provision Phoenix UAT environment",
                ],
            ))

        # ===== EPA DATA MODERNIZATION STORYLINE =====

        # W2: EPA requirements
        if w == 2:
            msgs.append(self._make_message(week, weekday=3,
                text=(
                    "EPA Data Modernization project is entering requirements phase. The client "
                    "(EPA Region 4) has strict regulatory requirements around data retention and "
                    "audit trails.\n\nPriya will lead the implementation. I need you to review "
                    "her architecture proposal by January 23. The data pipeline must be fully "
                    "operational by August 7 — that's a hard government deadline.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[
                        self._person("Robert Kim"),
                        self._person("Priya Patel"),
                    ],
                    projects=[self._project(EPA, priority="high")],
                    tasks=[
                        self._task("Review Priya's EPA architecture proposal", assignee="You",
                                   due_date="2026-01-23", priority="high", project=EPA,
                                   waiting_on="Priya Patel"),
                        self._task("Lead EPA implementation", assignee="Priya Patel",
                                   project=EPA, priority="high"),
                    ],
                    summary="EPA project requirements phase. Architecture review due Jan 23, hard deadline Aug 7.",
                ),
            ))

        # W8: EPA pipeline kickoff
        if w == 8:
            msgs.append(self._make_message(week, weekday=2,
                text=(
                    "EPA pipeline build phase starts this week. Priya has the architecture approved. "
                    "Here's the breakdown:\n"
                    "- Priya: Core ETL pipeline and data validation\n"
                    "- Marcus: Python extraction scripts for the legacy data\n"
                    "- You: Schema optimization and dbt model design\n\n"
                    "Marcus can't start until you finalize the Postgres schema. Target: March 13.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[
                        self._person("Robert Kim"),
                        self._person("Priya Patel"),
                        self._person("Marcus Webb"),
                    ],
                    projects=[self._project(EPA, priority="high")],
                    tasks=[
                        self._task("Build EPA core ETL pipeline", assignee="Priya Patel",
                                   project=EPA, priority="high"),
                        self._task("Write EPA legacy data extraction scripts", assignee="Marcus Webb",
                                   project=EPA, priority="high", waiting_on="You"),
                        self._task("Finalize EPA Postgres schema and dbt models", assignee="You",
                                   due_date="2026-03-13", priority="high", project=EPA),
                    ],
                    summary="EPA pipeline build starts. Schema due Mar 13, blocks Marcus's extraction work.",
                ),
            ))

        # W14: EPA mid-build status
        if w == 14:
            msgs.append(self._make_message(week, platform=Platform.SLACK,
                text=(
                    "EPA status check. Pipeline is behind schedule — Priya flagged data quality issues "
                    "in the legacy datasets. We may need to add a data cleansing step. Can you assess "
                    "impact to the schema by next Monday?"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim"), self._person("Priya Patel")],
                    projects=[self._project(EPA, status="blocked", priority="high")],
                    tasks=[
                        self._task("Assess EPA data quality impact on schema", assignee="You",
                                   due_date="2026-04-13", priority="high", project=EPA),
                    ],
                    summary="EPA behind schedule. Data quality issues, schema impact assessment needed.",
                ),
            ))

        # W22: EPA testing phase
        if w == 22:
            msgs.append(self._make_message(week,
                text=(
                    "EPA is entering testing phase. The pipeline is functional but we need to validate "
                    "against the EPA's test datasets. They've sent 3 test files.\n\n"
                    "Priya will run the tests. Marcus should help with edge case scripts. I need a "
                    "testing status report from you by June 12.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[
                        self._person("Robert Kim"),
                        self._person("Priya Patel"),
                        self._person("Marcus Webb"),
                    ],
                    projects=[self._project(EPA)],
                    tasks=[
                        self._task("Submit EPA testing status report", assignee="You",
                                   due_date="2026-06-12", priority="high", project=EPA),
                        self._task("Run EPA test dataset validation", assignee="Priya Patel",
                                   project=EPA, priority="high"),
                        self._task("Write EPA edge case test scripts", assignee="Marcus Webb",
                                   project=EPA, priority="medium", waiting_on="Priya Patel"),
                    ],
                    summary="EPA entering testing. Test dataset validation, status report due June 12.",
                ),
            ))

        # W30: EPA deployment
        if w == 30:
            msgs.append(self._make_message(week,
                text=(
                    "EPA deployment to staging is greenlit. Production deployment target is August 7 — "
                    "the hard government deadline. I need:\n"
                    "1. Staging deployment completed by July 31\n"
                    "2. Final data reconciliation report by August 4\n"
                    "3. Go-live sign-off from you and Priya\n\n"
                    "No room for slippage here.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim"), self._person("Priya Patel")],
                    projects=[self._project(EPA, priority="critical")],
                    tasks=[
                        self._task("Complete EPA staging deployment", assignee="You",
                                   due_date="2026-07-31", priority="critical", project=EPA),
                        self._task("Prepare EPA final data reconciliation report", assignee="You",
                                   due_date="2026-08-04", priority="critical", project=EPA),
                        self._task("Sign off on EPA go-live", assignee="Priya Patel",
                                   due_date="2026-08-07", priority="critical", project=EPA,
                                   waiting_on="You"),
                    ],
                    summary="EPA staging Jul 31, production Aug 7. Hard government deadline.",
                    tone=self._tone(urgency=1.0, escalation=True, temperature="neutral",
                                    deliverable=True, peer_progress=True),
                ),
            ))

        # W33: EPA go-live
        if w == 33:
            msgs.append(self._make_message(week,
                text=(
                    "EPA Data Modernization is live in production. The client confirmed the data "
                    "pipeline is running correctly. Great execution under pressure.\n\n"
                    "Priya — outstanding work leading this. Please both document the deployment "
                    "for the operations team by August 21.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim"), self._person("Priya Patel")],
                    projects=[self._project(EPA, status="completed")],
                    tasks=[
                        self._task("Document EPA deployment for operations", assignee="You",
                                   due_date="2026-08-21", priority="medium", project=EPA),
                    ],
                    summary="EPA is live. Deployment documentation due Aug 21.",
                ),
                resolves_tasks=[
                    "Complete EPA staging deployment",
                    "Sign off on EPA go-live",
                ],
            ))

        # ===== BIWEEKLY STATUS REQUESTS (both projects) =====
        if w in (5, 9, 12, 17, 21, 25, 29, 34, 39, 43, 47, 51):
            msgs.append(self._make_message(week, platform=Platform.SLACK, weekday=0, hour=10,
                text=(
                    f"Biweekly status update please. Quick bullets on Phoenix and EPA — "
                    f"where are we, any risks, anything I need to escalate?"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim")],
                    projects=[self._project(PHOENIX), self._project(EPA)],
                    tasks=[
                        self._task("Submit biweekly status update to Robert", assignee="You",
                                   priority="medium"),
                    ],
                    summary=f"Robert requests biweekly status update on both projects (W{w}).",
                ),
            ))

        # W45: Year-end retrospective
        if w == 45:
            msgs.append(self._make_message(week,
                text=(
                    "With both Phoenix and EPA shipped, I'd like to do a year-end retrospective. "
                    "Please prepare a summary of:\n"
                    "1. Key wins and what went well\n"
                    "2. What we'd do differently\n"
                    "3. Recommendations for 2027 project planning\n\n"
                    "Due by November 20.\n\nRobert"
                ),
                extraction=self._extraction(
                    people=[self._person("Robert Kim")],
                    projects=[self._project(PHOENIX), self._project(EPA)],
                    tasks=[
                        self._task("Prepare year-end project retrospective", assignee="You",
                                   due_date="2026-11-20", priority="medium"),
                    ],
                    summary="Year-end retrospective for Phoenix and EPA due Nov 20.",
                ),
            ))

        return msgs
