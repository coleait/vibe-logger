from vibelogger import create_file_logger

def fetch_user_profile(user_id: str) -> dict:
    logger = create_file_logger("user_service")
    
    logger.info(
        operation="fetchUserProfile",
        message=f"Starting profile fetch for user {user_id}",
        context={"user_id": user_id, "source": "user_service"}
    )
    
    try:
        if user_id == "invalid":
            raise ValueError("Invalid user ID format")
        
        if user_id == "missing":
            user_profile = None
        else:
            user_profile = {"id": user_id, "name": "John Doe", "email": "john@example.com"}
        
        if user_profile is None:
            logger.error(
                operation="fetchUserProfile",
                message="User profile not found in database",
                context={"user_id": user_id, "query": "SELECT * FROM users WHERE id = ?"},
                human_note="AI-TODO: Check if the user exists or if there's a database connection issue",
                ai_todo="Analyze the database query and suggest fixes for null results"
            )
            return None
        
        name = user_profile["name"]
        
        logger.info(
            operation="fetchUserProfile",
            message=f"Successfully fetched profile for {name}",
            context={"user_id": user_id, "profile_data": user_profile}
        )
        
        return user_profile
        
    except Exception as e:
        logger.log_exception(
            operation="fetchUserProfile",
            exception=e,
            context={"user_id": user_id, "attempted_action": "profile_fetch"},
            human_note="This error occurred during user profile fetching",
            ai_todo="Suggest proper error handling and validation for user_id parameter"
        )
        return None

if __name__ == "__main__":
    result1 = fetch_user_profile("user-123")
    print("=== SUCCESS CASE ===")
    
    result2 = fetch_user_profile("missing")
    print("=== MISSING USER CASE ===")
    
    result3 = fetch_user_profile("invalid")
    print("=== ERROR CASE ===")
    
    logger = create_file_logger("user_service")
    print("\n=== ALL LOGS FOR AI ===")
    print("Logs saved to:", logger.log_file)
    print(logger.get_logs_for_ai())