import streamlit as st
from dataclasses import dataclass
from typing import List, Tuple

# AWS Pricing Constants
LAMBDA_REQUEST_COST = 0.0000002  # $0.0000002 per request
LAMBDA_DURATION_COST = 0.0000166667  # $0.0000166667 per GB-second (128MB = 0.128GB)
EC2_HOURLY_COST = 0.0104  # t3.micro $0.0104 per hour
HOURS_PER_MONTH = 24 * 30  # 720 hours

@dataclass
class UserInput:
    monthly_requests: int
    execution_time_ms: float
    
    def validate(self) -> None:
        if self.monthly_requests <= 0:
            raise ValueError("Monthly requests must be positive")
        if self.execution_time_ms <= 0:
            raise ValueError("Execution time must be positive")

@dataclass
class CostAnalysis:
    lambda_cost: float
    ec2_cost: float
    lambda_tradeoffs: List[str]
    ec2_tradeoffs: List[str]
    
    def get_cheaper_option(self) -> str:
        return "Lambda" if self.lambda_cost < self.ec2_cost else "EC2"
    
    def get_recommendation(self) -> str:
        cheaper = self.get_cheaper_option()
        savings = abs(self.lambda_cost - self.ec2_cost)
        return f"{cheaper} (saves ${savings:.2f}/month)"

def calculate_lambda_cost(monthly_requests: int, execution_time_ms: float) -> float:
    """Calculate monthly Lambda cost based on requests and execution time"""
    # Request cost
    request_cost = monthly_requests * LAMBDA_REQUEST_COST
    
    # Duration cost (convert ms to seconds, assume 128MB = 0.128GB)
    execution_time_seconds = execution_time_ms / 1000
    gb_seconds = monthly_requests * execution_time_seconds * 0.128
    duration_cost = gb_seconds * LAMBDA_DURATION_COST
    
    return request_cost + duration_cost

def calculate_ec2_cost(monthly_requests: int, execution_time_ms: float) -> float:
    """Calculate monthly EC2 cost based on baseline t3.micro pricing"""
    # For simplicity, assume single t3.micro instance can handle the workload
    # In reality, this would need more sophisticated capacity planning
    base_cost = EC2_HOURLY_COST * HOURS_PER_MONTH
    return base_cost

def get_tradeoffs(service: str) -> List[str]:
    """Returns list of trade-offs for the given service"""
    if service.lower() == "lambda":
        return ["Cold Starts"]
    elif service.lower() == "ec2":
        return ["Management Overhead", "Idle Cost"]
    else:
        return []

def get_user_inputs() -> Tuple[int, float]:
    """Collect and validate user inputs from Streamlit widgets"""
    st.header("📊 Input Your Requirements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_requests = st.number_input(
            "Monthly Requests",
            min_value=1,
            value=100000,
            step=1000,
            help="Expected number of requests per month"
        )
    
    with col2:
        execution_time_ms = st.number_input(
            "Execution Time (ms)",
            min_value=1.0,
            value=200.0,
            step=10.0,
            help="Average execution time per request in milliseconds"
        )
    
    return int(monthly_requests), float(execution_time_ms)

def display_comparison(analysis: CostAnalysis) -> None:
    """Display comparison table and recommendation"""
    st.header("💰 Cost Comparison")
    
    # Cost comparison
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "AWS Lambda",
            f"${analysis.lambda_cost:.2f}/month",
            delta=f"${analysis.lambda_cost - analysis.ec2_cost:.2f}" if analysis.lambda_cost != analysis.ec2_cost else None
        )
    
    with col2:
        st.metric(
            "AWS EC2",
            f"${analysis.ec2_cost:.2f}/month",
            delta=f"${analysis.ec2_cost - analysis.lambda_cost:.2f}" if analysis.lambda_cost != analysis.ec2_cost else None
        )
    
    with col3:
        cheaper = analysis.get_cheaper_option()
        savings = abs(analysis.lambda_cost - analysis.ec2_cost)
        st.metric(
            "Recommendation",
            cheaper,
            delta=f"Saves ${savings:.2f}/month"
        )
    
    # Trade-offs table
    st.header("⚖️ Trade-offs Analysis")
    
    trade_off_data = {
        "Service": ["AWS Lambda", "AWS EC2"],
        "Monthly Cost": [f"${analysis.lambda_cost:.2f}", f"${analysis.ec2_cost:.2f}"],
        "Trade-offs": [
            ", ".join(analysis.lambda_tradeoffs) if analysis.lambda_tradeoffs else "None",
            ", ".join(analysis.ec2_tradeoffs) if analysis.ec2_tradeoffs else "None"
        ]
    }
    
    st.table(trade_off_data)
    
    # Detailed recommendation
    st.header("🎯 Final Recommendation")
    
    cheaper = analysis.get_cheaper_option()
    savings = abs(analysis.lambda_cost - analysis.ec2_cost)
    
    if cheaper == "Lambda":
        st.success(f"**Recommended: AWS Lambda**")
        st.write(f"💡 Lambda will save you **${savings:.2f} per month** compared to EC2.")
        st.warning("⚠️ **Consider**: Lambda has cold start latency which may affect performance for infrequent requests.")
    else:
        st.success(f"**Recommended: AWS EC2**")
        st.write(f"💡 EC2 will save you **${savings:.2f} per month** compared to Lambda.")
        st.warning("⚠️ **Consider**: EC2 requires management overhead and you pay for idle time when not processing requests.")

def main():
    """Main application function"""
    st.set_page_config(
        page_title="AWS Compute Referee",
        page_icon="⚖️",
        layout="wide"
    )
    
    st.title("⚖️ AWS Compute Referee")
    st.markdown("*A decision-support tool to help you choose between AWS Lambda and EC2*")
    
    st.markdown("---")
    
    try:
        # Get user inputs
        monthly_requests, execution_time_ms = get_user_inputs()
        
        # Validate inputs
        user_input = UserInput(monthly_requests, execution_time_ms)
        user_input.validate()
        
        # Calculate costs
        lambda_cost = calculate_lambda_cost(monthly_requests, execution_time_ms)
        ec2_cost = calculate_ec2_cost(monthly_requests, execution_time_ms)
        
        # Get trade-offs
        lambda_tradeoffs = get_tradeoffs("lambda")
        ec2_tradeoffs = get_tradeoffs("ec2")
        
        # Create analysis
        analysis = CostAnalysis(
            lambda_cost=lambda_cost,
            ec2_cost=ec2_cost,
            lambda_tradeoffs=lambda_tradeoffs,
            ec2_tradeoffs=ec2_tradeoffs
        )
        
        st.markdown("---")
        
        # Display results
        display_comparison(analysis)
        
    except ValueError as e:
        st.error(f"Input Error: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("*Built for DevOps Engineers and Startup Founders using AWS*")

if __name__ == "__main__":
    main()