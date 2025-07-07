# VibeCoding Logger Specification

**Version: 1.0**  
**Last Updated: 2025-07-07**

This document defines the common specification for VibeCoding Logger implementations across all programming languages.

## 🎯 Core Concept

VibeCoding Logger is designed specifically for AI-driven development where LLMs need rich, structured context to understand and debug code effectively. Unlike traditional human-readable logs, this creates "AI briefing packages" with comprehensive context, correlation tracking, and embedded human annotations.

## 📋 Log Entry Format

All VibeCoding Logger implementations MUST produce log entries that conform to this JSON schema:

### Required Fields

```json
{
  "timestamp": "2025-07-07T08:36:42.123Z",
  "level": "INFO",
  "correlation_id": "req_abc123",
  "operation": "fetchUserProfile",
  "message": "User profile retrieved successfully",
  "context": {},
  "environment": {}
}
```

### Optional Fields

```json
{
  "source": "user_service.py:42 in get_user_profile()",
  "stack_trace": "TypeError: Cannot read properties...",
  "human_note": "AI-TODO: Check if user exists before fetching",
  "ai_todo": "Analyze user lookup failures and suggest improvements"
}
```

## 🔧 Field Specifications

### timestamp
- **Type**: String (ISO 8601 format)
- **Required**: Yes
- **Format**: UTC timezone with millisecond precision
- **Example**: `"2025-07-07T08:36:42.123Z"`

### level
- **Type**: String (enum)
- **Required**: Yes
- **Values**: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`
- **Case**: UPPERCASE

### correlation_id
- **Type**: String
- **Required**: Yes
- **Purpose**: Links related operations across a request/session
- **Format**: UUID v4 recommended, any unique string accepted
- **Example**: `"req_abc123"`, `"550e8400-e29b-41d4-a716-446655440000"`

### operation
- **Type**: String
- **Required**: Yes
- **Purpose**: Describes what the code was trying to accomplish
- **Format**: camelCase or snake_case (language-specific)
- **Examples**: `"fetchUserProfile"`, `"processPayment"`, `"validateInput"`

### message
- **Type**: String
- **Required**: Yes
- **Purpose**: Human-readable description of the log event
- **Format**: Complete sentence, descriptive but concise
- **Example**: `"User profile retrieved successfully"`

### context
- **Type**: Object
- **Required**: Yes (can be empty object)
- **Purpose**: Structured data relevant to the operation
- **Content**: Function arguments, variables, state information
- **Example**: 
  ```json
  {
    "user_id": "123",
    "source": "api_endpoint",
    "query_duration_ms": 45
  }
  ```

### environment
- **Type**: Object
- **Required**: Yes
- **Purpose**: Runtime environment information for reproduction
- **Content**: Language version, OS, platform, architecture
- **Example**:
  ```json
  {
    "language": "python",
    "language_version": "3.11.0",
    "os": "Darwin",
    "platform": "darwin-arm64",
    "hostname": "MacBook-Pro.local"
  }
  ```

### source (optional)
- **Type**: String
- **Required**: No
- **Purpose**: Source code location where log was generated
- **Format**: `"filename:line in function()"`
- **Example**: `"user_service.py:42 in get_user_profile()"`

### stack_trace (optional)
- **Type**: String
- **Required**: No
- **Purpose**: Full stack trace for errors/exceptions
- **Format**: Language-specific stack trace format
- **When**: Automatically included for ERROR and CRITICAL levels

### human_note (optional)
- **Type**: String
- **Required**: No
- **Purpose**: Natural language instructions/notes for AI analysis
- **Format**: Complete sentence or phrase
- **Example**: `"AI-TODO: Check if user exists before fetching profile"`

### ai_todo (optional)
- **Type**: String
- **Required**: No
- **Purpose**: Specific analysis requests for AI
- **Format**: Complete sentence describing what AI should analyze
- **Example**: `"Analyze user lookup failures and suggest improvements"`

## 🎨 Language-Specific Implementation Guidelines

### API Design Principles

1. **Consistent Core API**: All languages should provide similar core methods
2. **Language Idioms**: Use language-specific naming conventions and patterns
3. **Framework Integration**: Provide seamless integration with popular frameworks
4. **Standard Library Compatibility**: Integrate with existing logging systems

### Core Methods (All Languages)

```
// Basic logging
debug(operation, message, options?)
info(operation, message, options?)
warning(operation, message, options?)
error(operation, message, options?)
critical(operation, message, options?)

// Exception logging
logException(operation, exception, options?)

// Utility methods
getLogsForAI(filter?)
clearLogs()
```

### Configuration Interface

All implementations should support:
- File output with automatic rotation
- Memory management options
- Environment variable configuration
- Framework-specific integration options

## 📊 File Format Standards

### File Naming
- Pattern: `vibe_YYYYMMDD_HHMMSS.log`
- Example: `vibe_20250707_143052.log`
- Location: `~/.vibe_logs/{project_name}/` by default

### File Content
- Format: One JSON object per line (JSONL)
- Encoding: UTF-8
- Line separator: `\n`

### Log Rotation
- Default: 10MB per file
- Configurable maximum file size
- Automatic timestamp-based rotation
- Keep rotated files for debugging history

## 🔄 Cross-Language Compatibility

### Log Format Compatibility
- All languages MUST produce logs that conform to the same JSON schema
- Field names MUST be identical across languages
- Timestamp format MUST be consistent (ISO 8601 UTC)

### Correlation ID Standards
- UUID v4 format recommended
- Must be unique per request/session
- Should be propagated across service boundaries
- Support for custom correlation ID injection

### Context Standards
- Use consistent field naming when possible
- Common context fields:
  - `user_id`: User identifier
  - `request_id`: Request identifier  
  - `session_id`: Session identifier
  - `ip_address`: Client IP address
  - `user_agent`: Client user agent
  - `duration_ms`: Operation duration in milliseconds

## 🧪 Testing Requirements

### Unit Tests
- Core logging functionality
- Configuration management
- File output and rotation
- Memory management
- Thread safety (where applicable)

### Integration Tests
- Framework integration
- Standard logging library compatibility
- Cross-language log format validation

### Performance Tests
- High-volume logging scenarios
- Memory usage under load
- File I/O performance
- Concurrent access patterns

## 📈 Version Compatibility

### Semantic Versioning
- Major: Breaking changes to log format or core API
- Minor: New features, backwards compatible
- Patch: Bug fixes, internal improvements

### Log Format Versioning
- Include format version in log metadata when schema changes
- Maintain backwards compatibility for at least 2 major versions
- Provide migration tools for format upgrades

## 🔒 Security Considerations

### Sensitive Data Protection
- Implement PII masking capabilities
- Provide hooks for custom data sanitization
- Avoid logging secrets, tokens, passwords by default
- Support configurable field blacklisting

### File Permissions
- Log files should have restricted permissions (600 or 644)
- Directory creation should respect umask
- Provide configuration for custom file permissions

## 🌐 Internationalization

### Character Encoding
- UTF-8 for all text content
- Support for Unicode in log messages and context
- Proper handling of multi-byte characters

### Timezone Handling
- Always use UTC for timestamps
- Support timezone conversion utilities
- Document timezone handling in examples

---

This specification serves as the foundation for all VibeCoding Logger implementations. Language-specific implementations may extend this specification but MUST NOT violate these core requirements.