# constants/bedrock_prompts.py

from enum import Enum
from typing import Dict, Optional, List

class EnergyDocumentElement(Enum):
    SAFETY = "safety_management"
    ASSET_INTEGRITY = "asset_integrity"
    INCIDENT_MANAGEMENT = "incident_management"
    ENVIRONMENTAL = "environmental"

class EnergySectorPrompts:
    # Enhanced base context with more specific guidance
    BASE_CONTEXT = """You are an expert energy sector document analyst specializing in harmonizing operational procedures, 
    standards, and policies between organizations. You are tasked with performing a detailed comparative analysis of the provided documents.
    
    Core Analysis Framework:
    1. Document Structure and Organization:
       - Compare document hierarchies and organization
       - Analyze completeness and comprehensiveness
       - Evaluate clarity and accessibility of information
       
    2. Regulatory Compliance:
       - Identify specific regulatory requirements
       - Compare compliance approaches
       - Analyze documentation requirements
       
    3. Risk Management:
       - Compare risk assessment methodologies
       - Analyze control measures
       - Evaluate monitoring and review processes
       
    4. Integration Considerations:
       - Identify potential conflicts
       - Highlight best practices
       - Note harmonization opportunities
       
    5. Implementation Requirements:
       - Compare resource needs
       - Analyze training requirements
       - Evaluate documentation needs"""

    # Enhanced element contexts with comprehensive requirements
    ELEMENT_CONTEXTS: Dict[EnergyDocumentElement, str] = {
        EnergyDocumentElement.ASSET_INTEGRITY: """Analyze asset integrity management systems with specific focus on:

        1. Asset Management Strategy:
           Critical Analysis Areas:
           - Maintenance and inspection strategies
           - Risk-based inspection approaches
           - Preventive vs. predictive maintenance
           - Asset lifecycle management
           - Critical equipment classification
           
           Comparison Requirements:
           - Strategy development methodologies
           - Risk assessment approaches
           - Resource allocation methods
           - Performance indicators
           - Documentation standards

        2. Equipment and Systems:
           Critical Analysis Areas:
           - Equipment classification systems
           - Criticality assessment methods
           - Performance standards
           - Reliability requirements
           - Redundancy approaches
           
           Comparison Requirements:
           - Classification criteria
           - Assessment methodologies
           - Performance metrics
           - Testing protocols
           - Documentation requirements

        3. Maintenance Programs:
           Critical Analysis Areas:
           - Maintenance scheduling
           - Work order management
           - Resource allocation
           - Quality control
           - Performance monitoring
           
           Comparison Requirements:
           - Program structures
           - Scheduling methodologies
           - Resource management
           - Quality standards
           - Documentation practices

        4. Integrity Monitoring:
           Critical Analysis Areas:
           - Condition monitoring
           - Performance tracking
           - Degradation assessment
           - Failure prediction
           - Data management
           
           Comparison Requirements:
           - Monitoring techniques
           - Data collection methods
           - Analysis approaches
           - Reporting standards
           - Action triggers

        5. Management Systems:
           Critical Analysis Areas:
           - System integration
           - Data management
           - Performance tracking
           - Continuous improvement
           - Change management
           
           Comparison Requirements:
           - System architectures
           - Integration approaches
           - Performance metrics
           - Improvement processes
           - Change protocols""",

        EnergyDocumentElement.INCIDENT_MANAGEMENT: """Analyze incident management systems with specific focus on:

        1. Incident Response:
           Critical Analysis Areas:
           - Initial response procedures
           - Emergency protocols
           - Communication systems
           - Resource mobilization
           - Stakeholder notification
           
           Comparison Requirements:
           - Response timelines
           - Protocol alignment
           - Resource requirements
           - Communication standards
           - Documentation needs

        2. Investigation Process:
           Critical Analysis Areas:
           - Investigation triggers
           - Team composition
           - Methodology selection
           - Evidence collection
           - Root cause analysis
           
           Comparison Requirements:
           - Investigation criteria
           - Team requirements
           - Process standards
           - Documentation methods
           - Analysis techniques

        3. Corrective Actions:
           Critical Analysis Areas:
           - Action development
           - Implementation planning
           - Effectiveness verification
           - Progress tracking
           - Close-out criteria
           
           Comparison Requirements:
           - Action standards
           - Implementation processes
           - Verification methods
           - Tracking systems
           - Documentation requirements

        4. Learning Management:
           Critical Analysis Areas:
           - Lesson identification
           - Knowledge sharing
           - Implementation tracking
           - Effectiveness measurement
           - System improvement
           
           Comparison Requirements:
           - Learning processes
           - Sharing methods
           - Implementation approaches
           - Measurement criteria
           - Improvement standards

        5. Performance Monitoring:
           Critical Analysis Areas:
           - KPI development
           - Data collection
           - Trend analysis
           - Performance review
           - System improvement
           
           Comparison Requirements:
           - Metric definitions
           - Collection methods
           - Analysis techniques
           - Review processes
           - Improvement approaches""",

        EnergyDocumentElement.ENVIRONMENTAL: """Analyze environmental management systems with specific focus on:

        1. Environmental Compliance:
           Critical Analysis Areas:
           - Regulatory requirements
           - Permit conditions
           - Monitoring programs
           - Reporting systems
           - Documentation management
           
           Comparison Requirements:
           - Compliance approaches
           - Monitoring methods
           - Reporting standards
           - Documentation systems
           - Management processes

        2. Emissions Management:
           Critical Analysis Areas:
           - Emission sources
           - Control measures
           - Monitoring systems
           - Reporting requirements
           - Improvement programs
           
           Comparison Requirements:
           - Control strategies
           - Monitoring techniques
           - Reporting methods
           - Improvement approaches
           - Documentation standards

        3. Waste Management:
           Critical Analysis Areas:
           - Waste classification
           - Handling procedures
           - Storage requirements
           - Disposal methods
           - Documentation systems
           
           Comparison Requirements:
           - Classification systems
           - Handling standards
           - Storage criteria
           - Disposal protocols
           - Record-keeping requirements

        4. Environmental Assessment:
           Critical Analysis Areas:
           - Impact assessment
           - Risk evaluation
           - Mitigation planning
           - Performance monitoring
           - System improvement
           
           Comparison Requirements:
           - Assessment methods
           - Evaluation criteria
           - Planning approaches
           - Monitoring systems
           - Improvement processes

        5. Stakeholder Management:
           Critical Analysis Areas:
           - Stakeholder identification
           - Communication planning
           - Engagement methods
           - Performance reporting
           - Feedback management
           
           Comparison Requirements:
           - Identification processes
           - Communication standards
           - Engagement approaches
           - Reporting methods
           - Management systems""",

        EnergyDocumentElement.SAFETY: """Analyze safety management systems with specific focus on:

        1. Safety Standards:
           Critical Analysis Areas:
           - Personal safety requirements
           - Process safety standards
           - Risk management systems
           - Performance metrics
           - Documentation requirements
           
           Comparison Requirements:
           - Standard alignment
           - Risk approaches
           - Metric definitions
           - Documentation systems
           - Management processes

        2. Safety Procedures:
           Critical Analysis Areas:
           - Work authorization
           - Permit systems
           - Job safety analysis
           - Emergency response
           - Safety communications
           
           Comparison Requirements:
           - Authorization processes
           - Permit requirements
           - Analysis methods
           - Response protocols
           - Communication standards

        3. Training Requirements:
           Critical Analysis Areas:
           - Competency assessment
           - Training programs
           - Certification requirements
           - Performance evaluation
           - Record management
           
           Comparison Requirements:
           - Assessment methods
           - Program content
           - Certification standards
           - Evaluation criteria
           - Documentation systems

        4. Safety Culture:
           Critical Analysis Areas:
           - Leadership commitment
           - Employee engagement
           - Behavioral programs
           - Performance recognition
           - Continuous improvement
           
           Comparison Requirements:
           - Program structures
           - Engagement methods
           - Recognition systems
           - Improvement processes
           - Measurement approaches

        5. Contractor Management:
           Critical Analysis Areas:
           - Qualification requirements
           - Performance standards
           - Oversight systems
           - Incident management
           - Documentation requirements
           
           Comparison Requirements:
           - Qualification criteria
           - Performance metrics
           - Oversight methods
           - Management processes
           - Documentation standards"""
    }

    # Enhanced Bedrock parameters for more consistent and detailed responses
    BEDROCK_PARAMS = {
        "anthropic_version": "bedrock-2024-02-29",
        "max_tokens": 4096,
        "temperature": 0.2,
        "top_p": 0.95,
        "stop_sequences": ["Human:", "Assistant:"]
    }

    @staticmethod
    def get_analysis_prompt(element_type: EnergyDocumentElement,
                          doc1: str,
                          doc2: str,
                          specific_focus: Optional[str] = None) -> str:
        """Generate enhanced analysis prompt for Bedrock"""
        
        prompt = f"""Context: {EnergySectorPrompts.BASE_CONTEXT}

Element Focus: {EnergySectorPrompts.ELEMENT_CONTEXTS[element_type]}

Required Analysis Structure:
1. Document Overview:
   - Summarize key aspects of each document
   - Note document structure and organization
   - Identify primary focus areas

2. Detailed Comparison:
   - Analyze specific requirements and standards
   - Compare methodologies and approaches
   - Evaluate documentation requirements
   - Note unique elements in each document

3. Gap Analysis:
   - Identify missing elements
   - Compare coverage depth
   - Note areas needing enhancement
   - Highlight complementary elements

4. Integration Considerations:
   - Note potential conflicts
   - Identify best practices
   - Suggest harmonization approaches
   - List implementation requirements

Document 1:
{doc1}

Document 2:
{doc2}

{specific_focus if specific_focus else ''}

If insufficient information is found:
1. Specify exactly which aspects lack adequate detail
2. Identify what additional information would be needed
3. Note any assumptions made in the analysis
4. Suggest specific areas where more documentation is required

Required Output Format:
1. Executive Summary
2. Detailed Comparison by Topic Area
3. Gap Analysis
4. Integration Recommendations
5. Additional Information Needs (if any)"""

        return prompt

    @staticmethod
    def create_bedrock_request(prompt: str) -> Dict:
        """Create enhanced formatted request for Bedrock"""
        return {
            **EnergySectorPrompts.BEDROCK_PARAMS,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }