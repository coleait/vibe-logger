/**
 * Basic usage example for VibeCoding Logger - TypeScript
 * 
 * This example demonstrates the core features of VibeCoding Logger
 * for AI-native logging in TypeScript/Node.js applications.
 */

import { createFileLogger, createLogger, VibeLoggerConfigManager } from '../src/index.js';

/**
 * Basic usage example
 */
async function basicUsageExample() {
  console.log('=== Basic Usage Example ===');

  // Create a file logger that auto-saves to timestamped files
  const logger = createFileLogger('basic-example');

  // Log with rich context for AI analysis
  await logger.info('user_authentication', 'User login attempt started', {
    context: {
      userId: 'user-123',
      loginMethod: 'oauth',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0...'
    },
    humanNote: 'Monitor for suspicious login patterns',
    aiTodo: 'Check if this IP has had multiple failed attempts recently'
  });

  // Log a successful operation
  await logger.info('user_authentication', 'User successfully authenticated', {
    context: {
      userId: 'user-123',
      sessionId: 'sess-abc-123',
      authDuration: '0.45s'
    }
  });

  // Log an error with exception details
  try {
    // Simulate a database error
    throw new Error('Connection timeout to user database');
  } catch (error) {
    await logger.logException('database_query', error, {
      context: {
        query: 'SELECT * FROM users WHERE id = ?',
        params: ['user-123'],
        timeout: 5000
      },
      humanNote: 'Database has been slow lately',
      aiTodo: 'Analyze database performance and suggest optimization'
    });
  }

  // Get logs formatted for AI consumption
  const aiContext = await logger.getLogsForAI();
  console.log('Logs for AI analysis:');
  console.log(JSON.stringify(JSON.parse(aiContext), null, 2));
}

/**
 * Advanced configuration example
 */
async function advancedConfigExample() {
  console.log('\n=== Advanced Configuration Example ===');

  // Custom configuration
  const logger = createLogger({
    logFile: './logs/advanced-example.log',
    maxFileSizeMb: 50,
    autoSave: true,
    keepLogsInMemory: true,
    maxMemoryLogs: 500,
    correlationId: 'request-abc-123'
  });

  // Log a complex operation
  await logger.info('api_request_processing', 'Processing POST /api/users', {
    context: {
      requestId: 'req-xyz-789',
      endpoint: '/api/users',
      method: 'POST',
      contentLength: 1024,
      headers: {
        'content-type': 'application/json',
        'user-agent': 'MyApp/1.0'
      },
      body: {
        name: 'John Doe',
        email: 'john@example.com'
      }
    },
    humanNote: 'New user registration flow'
  });

  // Log validation results
  await logger.warning('input_validation', 'Email format validation failed', {
    context: {
      field: 'email',
      value: 'invalid-email',
      validator: 'email-format-regex',
      expected: 'valid email format'
    },
    aiTodo: 'Suggest better error message for user'
  });

  console.log('Advanced logging completed. Check ./logs/advanced-example.log');
}

/**
 * Error handling patterns example
 */
async function errorHandlingExample() {
  console.log('\n=== Error Handling Example ===');

  const logger = createLogger({
    keepLogsInMemory: true,
    autoSave: false
  });

  // Handle different types of errors
  const errors = [
    new Error('Standard Error object'),
    'String error message',
    42,
    { customError: 'Object error', code: 500 },
    null,
    undefined
  ];

  for (const [index, error] of errors.entries()) {
    await logger.logException(`error_type_${index}`, error, {
      context: { errorIndex: index, errorType: typeof error },
      humanNote: `Testing error handling for ${typeof error} type`
    });
  }

  const logs = await logger.getLogs();
  console.log(`Logged ${logs.length} different error types`);
}

/**
 * Memory management example
 */
async function memoryManagementExample() {
  console.log('\n=== Memory Management Example ===');

  // Logger with small memory limit for demonstration
  const logger = createLogger({
    keepLogsInMemory: true,
    maxMemoryLogs: 5,
    autoSave: false
  });

  // Generate more logs than the memory limit
  for (let i = 1; i <= 10; i++) {
    await logger.info('memory_test', `Log entry ${i}`, {
      context: { iteration: i }
    });
  }

  const logs = await logger.getLogs();
  console.log(`Memory limit: 5, Generated: 10, Kept in memory: ${logs.length}`);
  console.log('Kept logs:', logs.map(log => log.context.iteration));
}

/**
 * Correlation tracking example
 */
async function correlationTrackingExample() {
  console.log('\n=== Correlation Tracking Example ===');

  const correlationId = `request-${Date.now()}`;
  const logger = createLogger({
    correlationId,
    keepLogsInMemory: true,
    autoSave: false
  });

  // Simulate a request flow with multiple operations
  await logger.info('request_start', 'HTTP request received', {
    context: { endpoint: '/api/orders', method: 'POST' }
  });

  await logger.info('auth_check', 'Validating user authentication', {
    context: { userId: 'user-456' }
  });

  await logger.info('business_logic', 'Processing order creation', {
    context: { productId: 'prod-789', quantity: 2 }
  });

  await logger.info('database_write', 'Saving order to database', {
    context: { orderId: 'order-321' }
  });

  await logger.info('request_complete', 'HTTP request completed', {
    context: { statusCode: 201, duration: '1.2s' }
  });

  // All logs will have the same correlation ID
  const logs = await logger.getLogs();
  console.log('Correlation ID for all logs:', logs[0].correlation_id);
  console.log('Request flow operations:', logs.map(log => log.operation));
}

/**
 * Run all examples
 */
async function runExamples() {
  try {
    await basicUsageExample();
    await advancedConfigExample();
    await errorHandlingExample();
    await memoryManagementExample();
    await correlationTrackingExample();
    
    console.log('\n✅ All examples completed successfully!');
  } catch (error) {
    console.error('❌ Example failed:', error);
    process.exit(1);
  }
}

// Run examples if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runExamples();
}