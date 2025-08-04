# ADR-002: Redis Pub/Sub Implementation for Event Bus

**Date**: 2024-01-01  
**Status**: Accepted  
**Deciders**: Development Team  
**Consulted**: Redis Community, Performance Engineers  
**Informed**: All Stakeholders

---

## 📝 Summary

Implement the event bus abstraction using Redis pub/sub with custom encoding and connection management.

---

## 🎯 Context and Problem Statement

### Background
Following ADR-001's decision to use event-driven architecture with Redis pub/sub, we need to determine the specific implementation details for the Redis event bus.

### Problem Statement
How should we implement the Redis event bus to provide:
- Reliable message delivery within Redis limitations
- Efficient serialization and deserialization
- Connection pooling and error handling
- Event tracing and monitoring integration

### Goals and Requirements
- Goal 1: Implement IEventBus interface using Redis pub/sub
- Goal 2: Handle connection failures gracefully
- Goal 3: Support event metadata for tracing and correlation
- Requirement 1: JSON serialization for cross-language compatibility
- Requirement 2: Connection pooling for performance
- Requirement 3: Integration with monitoring system

### Constraints
- Redis pub/sub fire-and-forget semantics (no durability)
- Must work with redis-py async client
- Need to handle datetime and UUID serialization
- Must support graceful shutdown

---

## 🔍 Decision Drivers

- **Performance**: Minimize serialization overhead
- **Reliability**: Handle Redis connection issues
- **Observability**: Track all events for monitoring
- **Maintainability**: Clean interface implementation
- **Compatibility**: JSON for interoperability
- **Scalability**: Connection pooling for high throughput

---

## 🛠️ Considered Options

### Option 1: Simple JSON + Single Connection
**Description**: Basic JSON serialization with single Redis connection

**Pros**:
- ✅ Simple implementation
- ✅ Easy to debug
- ✅ Minimal dependencies

**Cons**:
- ❌ No connection pooling
- ❌ Poor error handling
- ❌ Doesn't handle datetime/UUID serialization
- ❌ No graceful degradation

**Effort**: Low  
**Risk**: High

### Option 2: Custom Serialization + Connection Pool
**Description**: Custom JSON encoder with Redis connection pooling

**Pros**:
- ✅ Handles complex data types (datetime, UUID)
- ✅ Connection pooling for performance
- ✅ Better error handling
- ✅ Monitoring integration points

**Cons**:
- ❌ More complex implementation
- ❌ Custom encoding/decoding logic

**Effort**: Medium  
**Risk**: Low

### Option 3: MessagePack + Advanced Features
**Description**: Binary serialization with circuit breakers and retries

**Pros**:
- ✅ Faster serialization than JSON
- ✅ Smaller message size
- ✅ Advanced reliability features

**Cons**:
- ❌ Binary format harder to debug
- ❌ Additional dependencies
- ❌ Complexity may be overkill
- ❌ Cross-language compatibility issues

**Effort**: High  
**Risk**: Medium

---

## ✅ Decision Outcome

### Chosen Option
**Selected**: Option 2 - Custom JSON Serialization + Connection Pool

### Rationale
1. **JSON Compatibility**: Human-readable, cross-language support
2. **Custom Encoder**: Handles datetime and UUID serialization properly
3. **Connection Pooling**: Redis connection pooling for better performance
4. **Monitoring Integration**: Built-in hooks for event tracking
5. **Balanced Complexity**: Not too simple, not over-engineered

### Decision Criteria Evaluation
| Criteria | Simple JSON | Custom JSON+Pool | MessagePack | Winner |
|----------|-------------|------------------|-------------|---------|
| Implementation Speed | 9/10 | 6/10 | 4/10 | Simple JSON |
| Performance | 5/10 | 8/10 | 9/10 | MessagePack |
| Debuggability | 8/10 | 8/10 | 4/10 | Tie |
| Reliability | 3/10 | 8/10 | 9/10 | MessagePack |
| Maintainability | 7/10 | 8/10 | 5/10 | Custom JSON |
| **Weighted Score** | **6.4** | **7.6** | **6.2** | **Custom JSON** |

---

## 📈 Expected Consequences

### Positive Consequences
- ✅ Proper handling of Python datetime and UUID objects
- ✅ Good performance through connection pooling
- ✅ Human-readable JSON for debugging
- ✅ Integration points for monitoring and tracing
- ✅ Graceful handling of Redis connection issues

### Negative Consequences
- ❌ JSON serialization slower than binary formats
- ❌ Larger message sizes than binary serialization
- ❌ Custom encoder adds some complexity
- ❌ Still subject to Redis pub/sub delivery limitations

### Neutral Consequences
- ➖ Standard JSON format familiar to all developers
- ➖ Redis connection pooling is well-understood pattern

---

## 🔄 Implementation Plan

### Immediate Actions
1. **EventEncoder Class**: Custom JSON encoder for datetime/UUID
2. **RedisEventBus Class**: Implement IEventBus with Redis pub/sub
3. **Connection Management**: Async Redis client with connection pooling

### Timeline
- **Day 1**: EventEncoder and basic Redis connection
- **Day 2**: Pub/sub implementation with error handling
- **Day 3**: Monitoring integration and testing

### Success Metrics
- **Serialization**: Handle all Python types used in events
- **Performance**: <10ms event publish latency
- **Reliability**: Graceful handling of Redis disconnections

---

## 📊 Validation and Monitoring

### Validation Approach
- **Unit Tests**: Test EventEncoder with various data types
- **Integration Tests**: End-to-end event publishing and subscription
- **Error Injection**: Test behavior during Redis failures

### Monitoring Plan
- **Event Metrics**: Publish/subscribe rates and latencies
- **Connection Health**: Redis connection status and pool metrics
- **Error Tracking**: Serialization and connection errors

### Review Schedule
- **Short-term Review**: 2 weeks after implementation
- **Long-term Review**: 3 months after deployment
- **Trigger Events**: Performance issues or reliability problems

---

## 🔗 Related Decisions

### Supersedes
- None

### Superseded By
- None currently

### Related To
- [ADR-001]: Event-Driven Architecture (parent decision)
- [Future ADR]: Event durability patterns if needed

---

## 📚 References

### Documentation
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Python JSON Encoder](https://docs.python.org/3/library/json.html#json.JSONEncoder)

### External Resources
- [Redis Connection Pooling Best Practices](https://redis.com/blog/connection-pooling-best-practices/)
- [JSON Serialization Performance](https://pythonspeed.com/articles/json-memory-streaming/)

### Internal Resources
- IEventBus Interface Definition
- Event Schema Specification
- Monitoring Requirements Document

---

## 📝 Notes and Comments

### Discussion Notes
- Team agreed JSON debuggability outweighs MessagePack performance
- Connection pooling essential for production workloads
- Custom encoder needed for datetime objects in event metadata

### Future Considerations
- Consider Redis Streams if durability becomes requirement
- Evaluate Avro or Protocol Buffers for schema evolution
- Monitor JSON performance and optimize if needed

### Lessons Learned
- Balance simplicity with production requirements
- Custom encoders solve practical serialization issues
- Connection pooling is essential for Redis performance

---

## 🏷️ Tags
`#redis` `#event-bus` `#serialization` `#json` `#implementation`