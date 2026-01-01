from pyairtable import Api
import os

# Environment variables
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = "Symptoms"

# Airtable setup
airtable_api = Api(AIRTABLE_API_KEY)
airtable_table = airtable_api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# --- Inline normalized JSON ---
symptoms_data = [{
    "id":
    1,
    "symptom":
    "Chronic fatigue and exhaustion, even after rest",
    "keywords": [
        "fatigue", "exhaustion", "tired all the time", "drained", "no energy",
        "burnout tiredness"
    ],
    "long_tail_queries": [
        "Why do I feel exhausted even after sleeping 8 hours from work stress?",
        "Constant fatigue at job despite rest",
        "Work making me chronically tired"
    ],
    "patterns":
    "Mentions of persistent tiredness unrelated to activity level, references to rest not helping, linked to work demands"
}, {
    "id":
    2,
    "symptom":
    "Headaches, migraines, and visual disturbances",
    "keywords": [
        "headaches", "migraines", "eye strain", "blurry vision",
        "tension headache"
    ],
    "long_tail_queries": [
        "Work stress causing daily headaches and blurry eyes",
        "Migraines from job pressure",
        "Visual problems due to workplace tension"
    ],
    "patterns":
    "Complaints of head pain or vision issues tied to stress triggers, recurring during or after work"
}, {
    "id":
    3,
    "symptom":
    "Muscle tension, body aches, and musculoskeletal pain",
    "keywords": [
        "muscle tension", "body aches", "sore muscles", "back pain",
        "neck stiffness"
    ],
    "long_tail_queries": [
        "Work stress leading to constant muscle aches and tension",
        "Body pain from job anxiety",
        "Musculoskeletal issues in stressful office"
    ],
    "patterns":
    "Descriptions of physical tightness or soreness in muscles or joints, often worse under pressure"
}, {
    "id":
    4,
    "symptom":
    "Sleep disturbances, insomnia, or restless sleep",
    "keywords": [
        "insomnia", "can't sleep", "restless nights", "work insomnia",
        "sleep problems"
    ],
    "long_tail_queries": [
        "Can't sleep because of work thoughts racing",
        "Job stress causing insomnia every night",
        "Restless sleep from workplace worries"
    ],
    "patterns":
    "Issues with falling asleep, staying asleep, or poor sleep quality linked to work rumination"
}, {
    "id":
    5,
    "symptom":
    "Stomach issues, gastrointestinal problems, or upset stomach",
    "keywords": [
        "stomach ache", "GI issues", "upset stomach", "nausea from stress",
        "digestive problems"
    ],
    "long_tail_queries": [
        "Work stress giving me constant stomach problems",
        "Upset stomach and GI distress at job", "Nausea from workplace anxiety"
    ],
    "patterns":
    "Digestive complaints like pain, bloating, or nausea triggered by work events"
}, {
    "id":
    6,
    "symptom":
    "Heart-related issues such as pounding heart, chest pains, or cardiovascular strain",
    "keywords": [
        "pounding heart", "chest pain", "heart palpitations",
        "stress heart issues"
    ],
    "long_tail_queries": [
        "Work making my heart race and chest hurt",
        "Pounding heart from job pressure",
        "Cardiovascular strain due to workplace stress"
    ],
    "patterns":
    "Sensations of rapid heartbeat or chest discomfort during stressful work moments"
}, {
    "id":
    7,
    "symptom":
    "Increased susceptibility to illness or weakened immune system",
    "keywords": [
        "getting sick often", "weak immune system", "frequent colds",
        "stress illnesses"
    ],
    "long_tail_queries": [
        "Always getting sick because of work stress",
        "Job weakening my immune system",
        "Increased illness from workplace demands"
    ],
    "patterns":
    "Noting higher frequency of minor illnesses or feeling run-down attributed to chronic stress"
}, {
    "id":
    8,
    "symptom":
    "Anxiety, panic, constant fear, or overthinking",
    "keywords": [
        "anxiety", "panic attacks", "constant worry", "overthinking",
        "work anxiety"
    ],
    "long_tail_queries": [
        "Constant anxiety and overthinking at work", "Panic from job fears",
        "Workplace stress causing daily worry"
    ],
    "patterns":
    "Expressions of fear, rumination, or panic episodes related to work scenarios"
}, {
    "id":
    9,
    "symptom":
    "Depression, deep sadness, hopelessness, or low mood",
    "keywords":
    ["depression", "sadness", "hopelessness", "low mood", "work depression"],
    "long_tail_queries": [
        "Feeling hopeless and sad because of my job",
        "Work causing deep depression", "Low mood from workplace issues"
    ],
    "patterns":
    "Persistent feelings of sadness or despair connected to job dissatisfaction"
}, {
    "id":
    10,
    "symptom":
    "Irritability, mood swings, short temper, or emotional reactivity",
    "keywords": [
        "irritability", "mood swings", "short temper", "snappy",
        "emotional outbursts"
    ],
    "long_tail_queries": [
        "Work stress making me irritable and moody", "Short temper at job",
        "Emotional reactivity from workplace pressure"
    ],
    "patterns":
    "Quick changes in mood or heightened reactivity triggered by work interactions"
}, {
    "id":
    11,
    "symptom":
    "Emotional exhaustion, emptiness, or frequent breakdowns",
    "keywords": [
        "emotional exhaustion", "feeling empty", "breakdowns",
        "drained emotionally"
    ],
    "long_tail_queries": [
        "Emotional exhaustion from work leading to breakdowns",
        "Feeling empty inside due to job", "Frequent crying at work stress"
    ],
    "patterns":
    "Descriptions of being emotionally depleted or having meltdowns from accumulated stress"
}, {
    "id":
    12,
    "symptom":
    "Cynicism, negativity, pessimism, or detachment from work or life",
    "keywords":
    ["cynicism", "negativity", "pessimism", "detachment", "disengaged"],
    "long_tail_queries": [
        "Work making me cynical and negative about everything",
        "Feeling detached from job and life", "Pessimism from workplace stress"
    ],
    "patterns":
    "Negative outlook or emotional withdrawal specifically toward work or broader life"
}, {
    "id":
    13,
    "symptom":
    "Difficulty concentrating, mental fog, decision fatigue, or overthinking simple tasks",
    "keywords":
    ["concentration issues", "mental fog", "decision fatigue", "brain fog"],
    "long_tail_queries": [
        "Can't concentrate at work due to stress fog",
        "Decision fatigue from job demands",
        "Overthinking simple tasks because of anxiety"
    ],
    "patterns":
    "Struggles with focus, clarity, or making choices, often during work hours"
}, {
    "id":
    14,
    "symptom":
    "Burnout, feeling overwhelmed by small tasks, or loss of motivation or joy",
    "keywords":
    ["burnout", "overwhelmed", "no motivation", "loss of joy", "demotivated"],
    "long_tail_queries": [
        "Burnout at work making small tasks overwhelming",
        "Lost motivation and joy from job stress",
        "Feeling completely burned out"
    ],
    "patterns":
    "Overall exhaustion leading to aversion to tasks or lack of enthusiasm"
}, {
    "id":
    15,
    "symptom":
    "C-PTSD, dissociation, or feeling detached from reality or self",
    "keywords":
    ["C-PTSD", "dissociation", "detached from reality", "zoning out"],
    "long_tail_queries": [
        "Work trauma causing dissociation and detachment",
        "Feeling detached from myself due to job stress",
        "C-PTSD symptoms from workplace"
    ],
    "patterns":
    "Experiences of disconnection or trauma responses tied to work environment"
}, {
    "id":
    16,
    "symptom":
    "Heavy workload, unrealistic deadlines, or being swamped",
    "keywords":
    ["heavy workload", "unrealistic deadlines", "swamped", "overloaded"],
    "long_tail_queries": [
        "Overloaded with work and impossible deadlines",
        "Heavy workload stressing me out", "Feeling swamped at job every day"
    ],
    "patterns":
    "Complaints about volume of tasks or time pressures exceeding capacity"
}, {
    "id":
    17,
    "symptom":
    "Lack of work-life balance, long hours, or overtime",
    "keywords":
    ["work-life balance", "long hours", "overtime", "no boundaries"],
    "long_tail_queries": [
        "No work-life balance with constant overtime",
        "Long hours at job ruining my life",
        "Struggling with work encroaching on personal time"
    ],
    "patterns":
    "Blurring of work and personal life, excessive hours mentioned"
}, {
    "id":
    18,
    "symptom":
    "Toxic workplace culture, bullying, harassment, or negative relationships",
    "keywords":
    ["toxic culture", "bullying", "harassment", "negative relationships"],
    "long_tail_queries": [
        "Toxic workplace culture with bullying and harassment",
        "Negative relationships at job causing stress",
        "Dealing with workplace toxicity"
    ],
    "patterns":
    "References to harmful environment or interpersonal negativity"
}, {
    "id":
    19,
    "symptom":
    "Poor management support, micromanagement, or role confusion",
    "keywords": [
        "poor management", "micromanagement", "role confusion",
        "unsupportive boss"
    ],
    "long_tail_queries": [
        "Micromanagement and lack of support from boss",
        "Role confusion at work stressing me",
        "Poor leadership causing job issues"
    ],
    "patterns":
    "Issues with supervision, clarity of duties, or lack of guidance"
}, {
    "id":
    20,
    "symptom":
    "Job insecurity, fear of layoffs, or changes at work",
    "keywords":
    ["job insecurity", "fear of layoffs", "work changes", "unstable job"],
    "long_tail_queries": [
        "Constant fear of layoffs at work", "Job insecurity stressing me out",
        "Changes at workplace causing anxiety"
    ],
    "patterns":
    "Worries about employment stability or organizational shifts"
}, {
    "id":
    21,
    "symptom":
    "Meaningless or unfulfilling work, existential emptiness, or feeling replaceable",
    "keywords": [
        "meaningless work", "unfulfilling job", "existential emptiness",
        "replaceable"
    ],
    "long_tail_queries": [
        "Feeling my work is meaningless and unfulfilling",
        "Existential emptiness from job", "Like I'm replaceable at work"
    ],
    "patterns":
    "Lack of purpose or value in role, feelings of insignificance"
}, {
    "id":
    22,
    "symptom":
    "Pressure to perform, over-responsibility, or fear of rest or mistakes",
    "keywords": [
        "performance pressure", "over-responsibility", "fear of mistakes",
        "can't rest"
    ],
    "long_tail_queries": [
        "Constant pressure to perform perfectly at work",
        "Over-responsibility causing stress",
        "Fear of making mistakes or resting"
    ],
    "patterns":
    "High self-imposed or external expectations, avoidance of breaks"
}, {
    "id":
    23,
    "symptom":
    "Low morale, job dissatisfaction, or feeling trapped between peace and paycheck",
    "keywords": [
        "low morale", "job dissatisfaction", "feeling trapped",
        "paycheck vs peace"
    ],
    "long_tail_queries": [
        "Low morale and dissatisfaction at my job",
        "Feeling trapped between job and mental peace",
        "Work making me unhappy but need the money"
    ],
    "patterns":
    "Overall unhappiness or conflict between financial needs and well-being"
}, {
    "id":
    24,
    "symptom":
    "Relationship strain or carrying personal stress into work",
    "keywords":
    ["relationship strain", "personal stress at work", "spillover stress"],
    "long_tail_queries": [
        "Work stress straining my relationships",
        "Carrying personal issues into job",
        "Home stress affecting work performance"
    ],
    "patterns":
    "Crossover between personal life and work stressors"
}, {
    "id":
    25,
    "symptom":
    "Decreased performance, productivity dips, or forcing output with diminishing returns",
    "keywords": [
        "decreased performance", "productivity dips", "forcing work",
        "low output"
    ],
    "long_tail_queries": [
        "Work stress causing productivity to drop",
        "Forcing myself to work but getting less done",
        "Diminishing returns from job efforts"
    ],
    "patterns":
    "Noticing decline in efficiency or quality due to stress"
}, {
    "id":
    26,
    "symptom":
    "Difficult, toxic, or rude coworkers",
    "keywords": [
        "rude coworkers", "personality clashes", "gossip", "exclusion",
        "passive-aggressive"
    ],
    "long_tail_queries": [
        "Dealing with rude and toxic coworkers causing tension",
        "Personality clashes and gossip at work",
        "Feeling excluded in office cliques"
    ],
    "patterns":
    "Specific mentions of colleague behaviors like rudeness or exclusion"
}, {
    "id":
    27,
    "symptom":
    "Bullying, harassment, or mobbing",
    "keywords":
    ["bullying", "harassment", "mobbing", "verbal abuse", "ostracism"],
    "long_tail_queries": [
        "Workplace bullying and harassment making me anxious",
        "Being mobbed and undermined at job",
        "Verbal abuse from colleagues causing harm"
    ],
    "patterns":
    "Reports of targeted negative actions or exclusion leading to harm"
}, {
    "id":
    28,
    "symptom":
    "Micromanagement or over-controlling bosses",
    "keywords": [
        "micromanagement", "over-controlling boss", "constant updates",
        "eroded autonomy"
    ],
    "long_tail_queries": [
        "Micromanaging boss questioning everything I do",
        "Losing confidence from over-controlling supervisor",
        "Anxiety from boss demanding updates"
    ],
    "patterns":
    "Complaints about excessive oversight or loss of independence"
}, {
    "id":
    29,
    "symptom":
    "Poor or ineffective management or leadership",
    "keywords":
    ["poor leadership", "dismissive boss", "favoritism", "broken promises"],
    "long_tail_queries": [
        "Ineffective management with favoritism and no support",
        "Dismissive superiors breaking promises",
        "Frustration from inconsistent boss feedback"
    ],
    "patterns":
    "Issues with leadership quality, fairness, or reliability"
}, {
    "id":
    30,
    "symptom":
    "Conflicts and communication breakdowns",
    "keywords": [
        "conflicts", "communication breakdowns", "miscommunication",
        "unresolved grievances"
    ],
    "long_tail_queries": [
        "Constant conflicts and miscommunication at work",
        "Task disagreements causing stress fog",
        "Unresolved grievances with team"
    ],
    "patterns":
    "Mentions of arguments, misunderstandings, or lingering issues"
}, {
    "id":
    31,
    "symptom":
    "Interpersonal drama, politics, or power struggles",
    "keywords": [
        "interpersonal drama", "office politics", "power struggles",
        "favoritism"
    ],
    "long_tail_queries": [
        "Office politics and drama exhausting me",
        "Power struggles at work causing irritability",
        "Navigating unfair hierarchies in job"
    ],
    "patterns":
    "References to internal politics, competition, or unfair dynamics"
}, {
    "id":
    32,
    "symptom":
    "Emotional labor from others' issues",
    "keywords": [
        "emotional labor", "coworkers' stress", "venting overload",
        "spillover issues"
    ],
    "long_tail_queries": [
        "Emotional labor from coworkers venting all the time",
        "Dealing with others' stress at work adding to mine",
        "Coworker crying and issues spilling over"
    ],
    "patterns":
    "Absorbing or managing others' emotions without boundaries"
}, {
    "id":
    33,
    "symptom":
    "The Technical Identity Crisis (Maker vs Manager)",
    "keywords":
    ["no code today", "stuck in meetings", "maker vs manager", "rusty skills"],
    "long_tail_queries": [
        "Am I still a developer if I just sit in Jira all day?",
        "Depressed because I haven't committed code in a week",
        "Hate meetings want to build"
    ],
    "patterns":
    "Identity doubt or frustration from non-productive activities and interrupted creative flow"
}, {
    "id":
    34,
    "symptom":
    "The Date vs Reality Disconnect",
    "keywords": [
        "arbitrary deadlines", "estimation hell",
        "leadership oversimplification"
    ],
    "long_tail_queries": [
        "How to tell boss the estimate is impossible",
        "Anxiety from giving dates for unknown tech",
        "Manager demanding deadlines without requirements"
    ],
    "patterns":
    "Mismatched expectations on timelines and pressure for commitments on uncertain tasks"
}, {
    "id":
    35,
    "symptom":
    "The Input/Output Bottleneck (Executive Ghosting)",
    "keywords": [
        "boss ghosts me", "no feedback", "absentee manager",
        "blocked by leadership"
    ],
    "long_tail_queries": [
        "Why does my VP ignore my emails but panic in meetings?",
        "Stress from waiting on executive approval",
        "Dealing with a ghost boss"
    ],
    "patterns":
    "Inconsistent communication from superiors causing workflow blocks or escalations"
}, {
    "id":
    36,
    "symptom":
    "The Turf War Tension (Role Silos)",
    "keywords": [
        "design vs engineering", "product overstepping", "silo wars",
        "turf battles"
    ],
    "long_tail_queries": [
        "Fighting with product manager about implementation",
        "Designers ignoring technical constraints",
        "Exhausted by cross-functional arguments"
    ],
    "patterns":
    "Inter-team disputes over ownership leading to stalled progress"
}, {
    "id":
    37,
    "symptom":
    "The Analysis Paralysis Loop",
    "keywords": [
        "overanalyzing", "can't decide", "fear of wrong choice",
        "analysis paralysis"
    ],
    "long_tail_queries": [
        "Stuck in analysis paralysis on architecture",
        "Terrified to merge PR because of potential bugs",
        "Team debating same decision for weeks"
    ],
    "patterns":
    "Repetitive thought loops or indecision causing fear-driven delays"
}, {
    "id":
    38,
    "symptom":
    "The Misunderstood Neuro-difference",
    "keywords":
    ["fidgeting", "interrupting", "ADHD masking", "can't sit still"],
    "long_tail_queries": [
        "Boss says I'm rude for pacing on zoom",
        "I keep interrupting people because I'm excited",
        "Trouble sitting still in long architecture reviews"
    ],
    "patterns":
    "Misjudged behaviors linked to neurodivergence causing social friction or self-doubt"
}, {
    "id":
    39,
    "symptom":
    "The Swoop and Poop (Seagull Management)",
    "keywords": ["seagull manager", "last minute changes", "interference"],
    "long_tail_queries": [
        "Director changed everything right before launch",
        "Dealing with a boss who only critiques but doesn't help",
        "Seagull management destroying team velocity"
    ],
    "patterns":
    "Sudden disruptive interventions from uninvolved leaders"
}, {
    "id":
    40,
    "symptom":
    "The Data-less Dictator (HiPPO Decision Making)",
    "keywords":
    ["arrogant boss", "ignored data", "HiPPO", "authority decisions"],
    "long_tail_queries": [
        "How to argue with an arrogant senior leader",
        "Building a feature I know will fail because VP wants it",
        "Data being ignored for opinions"
    ],
    "patterns":
    "Authority overriding evidence-based input leading to forced execution"
}]
# --- End inline JSON ---

# Populate the table
for symptom in symptoms_data:
  try:
    record = {
        "ID": symptom["id"],
        "Symptom": symptom["symptom"],
        "Keywords": "\n".join(symptom["keywords"]),
        "LongTailQueries": "\n".join(symptom["long_tail_queries"]),
        "Patterns": symptom["patterns"]
    }

    airtable_table.create(record)
    print(f"Added: {record['Symptom']}")

  except Exception as e:
    print(f"Error adding {symptom.get('symptom')}: {str(e)}")

print("Population complete!")
