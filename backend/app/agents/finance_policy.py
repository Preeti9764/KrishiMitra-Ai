import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..models.schemas import AdvisoryRequest, AgentRecommendation


class FinancePolicyAgent:
    """Finance and Policy Agent using NLP retrieval for finding relevant schemes and loans"""
    
    def __init__(self):
        # Government schemes database
        self.schemes_database = {
            "pm_kisan": {
                "name": "PM-KISAN",
                "description": "Direct income support of Rs. 6000 per year to farmers",
                "eligibility": ["Small and marginal farmers", "Landholding up to 2 hectares"],
                "benefit_amount": "Rs. 6000 per year",
                "application_process": "Online through PM-KISAN portal",
                "keywords": ["income support", "direct benefit", "small farmers", "marginal farmers"],
                "category": "income_support"
            },
            "pm_fasal_bima": {
                "name": "PM Fasal Bima Yojana",
                "description": "Crop insurance scheme to protect farmers against natural calamities",
                "eligibility": ["All farmers", "All crops"],
                "benefit_amount": "Up to 100% of sum insured",
                "application_process": "Through banks or insurance companies",
                "keywords": ["crop insurance", "natural calamities", "risk protection", "insurance"],
                "category": "insurance"
            },
            "kisan_credit_card": {
                "name": "Kisan Credit Card",
                "description": "Credit facility for farmers to meet agricultural needs",
                "eligibility": ["All farmers", "Good credit history"],
                "benefit_amount": "Up to Rs. 3 lakhs",
                "application_process": "Through banks and cooperative societies",
                "keywords": ["credit", "loan", "agricultural finance", "banking"],
                "category": "credit"
            },
            "pm_ksy": {
                "name": "PM-KSY (Kisan Sampada Yojana)",
                "description": "Scheme for food processing and value addition",
                "eligibility": ["Farmers", "FPOs", "Agri-entrepreneurs"],
                "benefit_amount": "Up to 50% subsidy on project cost",
                "application_process": "Online through Ministry of Food Processing",
                "keywords": ["food processing", "value addition", "agri-business", "subsidy"],
                "category": "subsidy"
            },
            "soil_health_card": {
                "name": "Soil Health Card Scheme",
                "description": "Free soil testing and recommendations",
                "eligibility": ["All farmers"],
                "benefit_amount": "Free soil testing",
                "application_process": "Through agriculture department",
                "keywords": ["soil testing", "soil health", "nutrient management", "free"],
                "category": "testing"
            },
            "pm_ksn": {
                "name": "PM-KSN (Kisan Samman Nidhi)",
                "description": "Additional income support for farmers",
                "eligibility": ["PM-KISAN beneficiaries"],
                "benefit_amount": "Additional Rs. 2000 per year",
                "application_process": "Automatic for PM-KISAN beneficiaries",
                "keywords": ["additional support", "income", "pm-kisan", "benefit"],
                "category": "income_support"
            }
        }
        
        # Loan schemes database
        self.loan_schemes = {
            "agricultural_term_loan": {
                "name": "Agricultural Term Loan",
                "description": "Long-term loan for agricultural investments",
                "interest_rate": "8.5% - 12%",
                "tenure": "3-15 years",
                "amount": "Up to Rs. 10 lakhs",
                "collateral": "Land mortgage",
                "keywords": ["term loan", "long term", "investment", "land"],
                "category": "term_loan"
            },
            "crop_loan": {
                "name": "Crop Loan",
                "description": "Short-term loan for crop production",
                "interest_rate": "7% - 9%",
                "tenure": "6-18 months",
                "amount": "Up to Rs. 3 lakhs",
                "collateral": "Minimal",
                "keywords": ["crop", "short term", "production", "seasonal"],
                "category": "crop_loan"
            },
            "dairy_loan": {
                "name": "Dairy Loan",
                "description": "Loan for dairy farming and livestock",
                "interest_rate": "8% - 11%",
                "tenure": "3-7 years",
                "amount": "Up to Rs. 5 lakhs",
                "collateral": "Livestock/assets",
                "keywords": ["dairy", "livestock", "animal husbandry", "farming"],
                "category": "livestock_loan"
            },
            "farm_mechanization_loan": {
                "name": "Farm Mechanization Loan",
                "description": "Loan for purchasing farm machinery",
                "interest_rate": "9% - 13%",
                "tenure": "3-8 years",
                "amount": "Up to Rs. 15 lakhs",
                "collateral": "Machinery/assets",
                "keywords": ["machinery", "equipment", "mechanization", "tractor"],
                "category": "equipment_loan"
            }
        }
    
    async def recommend(self, request: AdvisoryRequest) -> AgentRecommendation:
        """Generate finance and policy recommendations"""
        # Analyze farmer profile for scheme eligibility
        eligibility_analysis = self._analyze_eligibility(request)
        
        # Find relevant schemes
        relevant_schemes = self._find_relevant_schemes(request, eligibility_analysis)
        
        # Find relevant loans
        relevant_loans = self._find_relevant_loans(request, eligibility_analysis)
        
        # Generate tasks
        tasks = self._generate_finance_tasks(relevant_schemes, relevant_loans, request)
        
        # Calculate priority and confidence
        priority = self._determine_priority(request, relevant_schemes, relevant_loans)
        confidence = self._calculate_confidence(request, eligibility_analysis)
        
        return AgentRecommendation(
            agent="finance_policy",
            priority=priority,
            confidence_score=confidence,
            summary=f"Financial schemes and loan opportunities for {request.profile.crop} farming",
            explanation=self._generate_explanation(relevant_schemes, relevant_loans),
            data_sources=["Government Schemes Database", "Banking Regulations", "Agricultural Policy Database"],
            tasks=tasks,
            risk_level="low",
            estimated_impact="positive",
            cost_estimate=self._estimate_benefits(relevant_schemes, relevant_loans),
            details={
                "schemes": relevant_schemes,
                "loans": relevant_loans,
                "eligibility": eligibility_analysis
            }
        )
    
    def _analyze_eligibility(self, request: AdvisoryRequest) -> Dict[str, Any]:
        """Analyze farmer eligibility for various schemes"""
        eligibility = {
            "farmer_category": self._categorize_farmer(request),
            "land_holding": request.profile.farm_size_hectares or 0,
            "crop_type": request.profile.crop,
            "location": f"{request.profile.state or 'Unknown'}, {request.profile.district or 'Unknown'}",
            "eligible_schemes": [],
            "eligible_loans": []
        }
        
        # Check PM-KISAN eligibility
        if eligibility["land_holding"] <= 2.0:
            eligibility["eligible_schemes"].append("pm_kisan")
        
        # Check general scheme eligibility
        eligibility["eligible_schemes"].extend(["pm_fasal_bima", "soil_health_card", "kisan_credit_card"])
        
        # Check loan eligibility
        eligibility["eligible_loans"].extend(["crop_loan", "agricultural_term_loan"])
        
        # Check for specific crop-based schemes
        if request.profile.crop in ["wheat", "rice", "maize"]:
            eligibility["eligible_schemes"].append("pm_ksy")
        
        return eligibility
    
    def _categorize_farmer(self, request: AdvisoryRequest) -> str:
        """Categorize farmer based on land holding"""
        land_holding = request.profile.farm_size_hectares or 0
        
        if land_holding <= 1.0:
            return "marginal"
        elif land_holding <= 2.0:
            return "small"
        elif land_holding <= 5.0:
            return "medium"
        else:
            return "large"
    
    def _find_relevant_schemes(self, request: AdvisoryRequest, eligibility: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find relevant government schemes using NLP retrieval"""
        relevant_schemes = []
        
        # Search based on eligibility
        for scheme_id in eligibility["eligible_schemes"]:
            if scheme_id in self.schemes_database:
                scheme = self.schemes_database[scheme_id].copy()
                scheme["relevance_score"] = self._calculate_scheme_relevance(scheme, request, eligibility)
                relevant_schemes.append(scheme)
        
        # Search based on keywords and context
        context_keywords = self._extract_context_keywords(request)
        for scheme_id, scheme in self.schemes_database.items():
            if scheme_id not in eligibility["eligible_schemes"]:
                relevance_score = self._calculate_keyword_relevance(scheme, context_keywords)
                if relevance_score > 0.3:  # Threshold for relevance
                    scheme_copy = scheme.copy()
                    scheme_copy["relevance_score"] = relevance_score
                    relevant_schemes.append(scheme_copy)
        
        # Sort by relevance and return top 5
        relevant_schemes.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_schemes[:5]
    
    def _find_relevant_loans(self, request: AdvisoryRequest, eligibility: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find relevant loan schemes"""
        relevant_loans = []
        
        # Search based on eligibility
        for loan_id in eligibility["eligible_loans"]:
            if loan_id in self.loan_schemes:
                loan = self.loan_schemes[loan_id].copy()
                loan["relevance_score"] = self._calculate_loan_relevance(loan, request, eligibility)
                relevant_loans.append(loan)
        
        # Search based on context
        context_keywords = self._extract_context_keywords(request)
        for loan_id, loan in self.loan_schemes.items():
            if loan_id not in eligibility["eligible_loans"]:
                relevance_score = self._calculate_keyword_relevance(loan, context_keywords)
                if relevance_score > 0.3:
                    loan_copy = loan.copy()
                    loan_copy["relevance_score"] = relevance_score
                    relevant_loans.append(loan_copy)
        
        # Sort by relevance and return top 3
        relevant_loans.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_loans[:3]
    
    def _extract_context_keywords(self, request: AdvisoryRequest) -> List[str]:
        """Extract keywords from request context"""
        keywords = []
        
        # Add crop-related keywords
        keywords.append(request.profile.crop)
        
        # Add farming practice keywords
        if request.profile.farming_practice:
            keywords.append(request.profile.farming_practice)
        
        # Add irrigation type keywords
        if request.profile.irrigation_type:
            keywords.append(request.profile.irrigation_type)
        
        # Add growth stage keywords
        if request.profile.growth_stage:
            keywords.append(request.profile.growth_stage)
        
        return keywords
    
    def _calculate_scheme_relevance(self, scheme: Dict[str, Any], request: AdvisoryRequest, eligibility: Dict[str, Any]) -> float:
        """Calculate relevance score for a scheme"""
        score = 0.5  # Base score
        
        # Higher score for eligible schemes
        if scheme["name"] in [self.schemes_database[s]["name"] for s in eligibility["eligible_schemes"]]:
            score += 0.3
        
        # Higher score for income support schemes for small farmers
        if eligibility["farmer_category"] in ["marginal", "small"] and scheme["category"] == "income_support":
            score += 0.2
        
        # Higher score for insurance schemes if weather risk is high
        if scheme["category"] == "insurance":
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_loan_relevance(self, loan: Dict[str, Any], request: AdvisoryRequest, eligibility: Dict[str, Any]) -> float:
        """Calculate relevance score for a loan"""
        score = 0.5  # Base score
        
        # Higher score for crop loans during growing season
        if loan["category"] == "crop_loan" and request.profile.growth_stage in ["sowing", "vegetative"]:
            score += 0.3
        
        # Higher score for term loans for medium/large farmers
        if loan["category"] == "term_loan" and eligibility["farmer_category"] in ["medium", "large"]:
            score += 0.2
        
        # Higher score for equipment loans if farm size is large
        if loan["category"] == "equipment_loan" and eligibility["land_holding"] > 5.0:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_keyword_relevance(self, item: Dict[str, Any], keywords: List[str]) -> float:
        """Calculate relevance based on keyword matching"""
        if "keywords" not in item:
            return 0.0
        
        item_keywords = [kw.lower() for kw in item["keywords"]]
        context_keywords = [kw.lower() for kw in keywords]
        
        matches = 0
        for context_kw in context_keywords:
            for item_kw in item_keywords:
                if context_kw in item_kw or item_kw in context_kw:
                    matches += 1
        
        return min(1.0, matches / len(item_keywords)) if item_keywords else 0.0
    
    def _generate_finance_tasks(self, schemes: List[Dict[str, Any]], loans: List[Dict[str, Any]], request: AdvisoryRequest) -> List[str]:
        """Generate tasks for finance and policy recommendations"""
        tasks = []
        
        # Add scheme-related tasks
        if schemes:
            top_scheme = schemes[0]
            tasks.append(f"Apply for {top_scheme['name']} - {top_scheme['benefit_amount']}")
            tasks.append(f"Application process: {top_scheme['application_process']}")
            
            # Add eligibility check task
            if "eligibility" in top_scheme:
                tasks.append(f"Check eligibility: {', '.join(top_scheme['eligibility'][:2])}")
        
        # Add loan-related tasks
        if loans:
            top_loan = loans[0]
            tasks.append(f"Consider {top_loan['name']} - Interest rate: {top_loan['interest_rate']}")
            tasks.append(f"Loan amount: {top_loan['amount']}, Tenure: {top_loan['tenure']}")
        
        # Add general tasks
        tasks.append("Visit nearest bank branch for detailed information")
        tasks.append("Keep required documents ready (Aadhaar, land records, bank passbook)")
        tasks.append("Check online portals for scheme updates")
        
        return tasks[:6]  # Limit to 6 tasks
    
    def _determine_priority(self, request: AdvisoryRequest, schemes: List[Dict[str, Any]], loans: List[Dict[str, Any]]) -> int:
        """Determine priority level"""
        # High priority if farmer is small/marginal and eligible for income support
        if request.profile.farm_size_hectares and request.profile.farm_size_hectares <= 2.0:
            return 8
        
        # Medium priority for other cases
        return 6
    
    def _calculate_confidence(self, request: AdvisoryRequest, eligibility: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        confidence = 0.8  # Base confidence
        
        # Higher confidence with more farmer information
        if request.profile.farm_size_hectares:
            confidence += 0.1
        
        if request.profile.state:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _estimate_benefits(self, schemes: List[Dict[str, Any]], loans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate financial benefits"""
        total_benefits = 0
        scheme_benefits = []
        
        for scheme in schemes[:3]:  # Top 3 schemes
            if "benefit_amount" in scheme:
                benefit_str = scheme["benefit_amount"]
                # Extract numeric value (simplified)
                if "Rs." in benefit_str:
                    try:
                        amount = float(re.findall(r'\d+', benefit_str)[0])
                        if "per year" in benefit_str.lower():
                            amount *= 12  # Monthly to yearly
                        total_benefits += amount
                        scheme_benefits.append({
                            "scheme": scheme["name"],
                            "benefit": benefit_str
                        })
                    except:
                        pass
        
        return {
            "total_annual_benefits_inr": total_benefits * 1000,  # Convert to INR
            "scheme_benefits": scheme_benefits,
            "loan_opportunities": len(loans),
            "benefit_unit": "INR per year"
        }
    
    def _generate_explanation(self, schemes: List[Dict[str, Any]], loans: List[Dict[str, Any]]) -> str:
        """Generate human-readable explanation"""
        if not schemes and not loans:
            return "No relevant schemes or loans found for current profile."
        
        explanation_parts = []
        
        if schemes:
            top_scheme = schemes[0]
            explanation_parts.append(f"Top scheme: {top_scheme['name']} - {top_scheme['description']}")
        
        if loans:
            top_loan = loans[0]
            explanation_parts.append(f"Recommended loan: {top_loan['name']} at {top_loan['interest_rate']} interest")
        
        explanation_parts.append(f"Found {len(schemes)} relevant schemes and {len(loans)} loan options.")
        
        return " ".join(explanation_parts)
