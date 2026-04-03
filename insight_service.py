def generate_insight(reading_level, attention_level, behavior_level, age):
    """
    Computes a comprehensive paragraph-length personalized analysis based on clinical risk levels.
    Levels are combinations of 'Low', 'Medium', 'High' risk.
    Note: High risk means lower capability. 
    """
    
    # Analyze reading / dyslexia traits
    reading_insight = ""
    if reading_level == "High":
        reading_insight = (
            "Severe indicators of phonological processing difficulty were observed. "
            "The student shows marked hesitation in identifying phonemes and associating "
            "symbols with sounds, which strongly correlates with Dyslexia. "
            "We highly recommend multisensory reading interventions and extended time for tasks."
        )
    elif reading_level == "Medium":
        reading_insight = (
            "Moderate reading fluency variations detected. The student occasionally "
            "struggles with rapid automized naming or word decoding, showing mild signs "
            "of dyslexic traits. Focused phonetic exercises and guided reading should be introduced."
        )
    else:
        reading_insight = (
            "Reading fluency and phonological processing appear within expected developmental ranges. "
            "No significant indicators of Dyslexia were identified during this assessment."
        )

    # Analyze attention / ADHD traits
    adhd_insight = ""
    if attention_level == "High" and behavior_level == "High":
        adhd_insight = (
            "Furthermore, critical flags for ADHD (Combined Type) are present. "
            "The test recorded significant inattentiveness, high impulsivity, and severe lack of executive function "
            "during sustained tasks. The child struggled to filter distractions and filter impulses. "
            "A professional evaluation by a pediatric neurologist or psychiatrist is strongly advised, "
            "along with a highly structured classroom environment."
        )
    elif attention_level == "High" or behavior_level == "High":
        adhd_insight = (
            "Additionally, the assessment flags elevated ADHD indicators. "
            "There were clear instances of either severe scattered attention or significant impulsivity. "
            "Behavioral redirection and environment structuring (like strategic seating) will be beneficial. "
            "Consider engaging the child in small, micro-burst learning sessions to maintain focus."
        )
    elif attention_level == "Medium" or behavior_level == "Medium":
        adhd_insight = (
            "Additionally, some attentional drift and minor impulsivity were noted. "
            "While not severe enough to definitively indicate ADHD, the child may benefit from "
            "regular sensory breaks, checklists, and clear, gamified task structures."
        )
    else:
        adhd_insight = (
            "Additionally, executive function and sustained attention were excellent. "
            "The student demonstrated strong impulse control and focus."
        )

    # Conclusion based on age
    conclusion = ""
    if age <= 7:
        conclusion = "Given the young age, neuroplasticity is very high. Early intervention and play-based therapies are highly effective."
    elif age <= 12:
        conclusion = "At this developmental stage, introducing structured routines and self-advocacy skills alongside academic support is crucial."
    else:
        conclusion = "For an adolescent, focusing on executive functioning tools, time management, and accommodations for testing will greatly support their academic journey."

    return f"{reading_insight}\n\n{adhd_insight}\n\n{conclusion}"

