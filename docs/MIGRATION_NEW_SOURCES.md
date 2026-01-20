# Migration Guide: Expanded Data Sources

## Quick Start

Your AI World Tracker now has **70+ data sources** (up from 30). Here's what you need to know:

## What Changed

### ✅ Automatic Changes (No Action Needed)
- New RSS feeds added automatically
- YouTube channels integrated via RSS
- Medium articles included
- AI newsletters active
- Reddit communities monitored
- Papers with Code integration
- Bilibili videos (Chinese content)

### ⚙️ Configuration Updates
Your [config.yaml](c:\AI_Tracker\ai-world-tracker\config.yaml) has been updated with new limits:
- `max_total`: 100 → 150 items
- `news_count`: 25 → 35 items
- `developer_count`: 20 → 30 items
- `community_count`: 10 → 25 items
- Plus 5 new counters for specific sources

## Testing the New Sources

### Option 1: Run Test Script (Recommended)
```powershell
python tests/test_new_sources.py
```

This will:
- Test each new source individually
- Run full collection with all sources
- Show performance metrics
- Verify all new sources are working

### Option 2: Quick Collection Test
```powershell
python -c "from data_collector import AIDataCollector; c = AIDataCollector(); d = c.collect_all(); print(f'Collected {sum(len(v) for v in d.values())} items')"
```

### Option 3: Run Main Program
```powershell
python TheWorldOfAI.py
```

## What to Expect

### Collection Time
- **Before**: 20-25 seconds
- **After**: 25-40 seconds
- **Reason**: 40+ more sources, but still efficient

### Item Counts
- **Before**: ~100 items total
- **After**: ~150 items total
- **Distribution**: More diverse sources

### New Content Types
You'll now see items from:
- 📱 Reddit discussions
- 🎥 YouTube AI channels
- 📝 Medium articles
- 📧 AI newsletters
- 📹 Bilibili videos (Chinese)
- 📄 Papers with Code
- And 10+ new RSS feeds

## Monitoring & Troubleshooting

### Check Collection Status
After running collection, check the console output for:
```
📡 启动并发采集任务...
⚡ 并发执行 XX 个采集任务
[████████████████████] 100%
```

### Failed Sources Summary
The collector will show any failed sources at the end:
```
⚠️ 失败的数据源 (X个):
  - Source Name (Category): Error message
```

### Common Issues

**1. Rate Limiting**
- **Symptom**: Some sources return 0 items
- **Solution**: Wait a few minutes, try again
- **Prevention**: Limits are pre-configured, but some APIs have hourly quotas

**2. Network Timeouts**
- **Symptom**: Collection takes longer or shows timeout errors
- **Solution**: Check internet connection
- **Config**: Adjust `request_timeout` in config.yaml if needed

**3. Empty Results**
- **Symptom**: Specific source returns 0 items
- **Reason**: May be recent content only, or source temporarily down
- **Action**: Check `_bmad-output/planning-artifacts/` logs

## Performance Tuning

### If Collection is Too Slow
Edit [config.yaml](c:\AI_Tracker\ai-world-tracker\config.yaml):
```yaml
async_collector:
  max_concurrent_requests: 20  # Increase to 25-30
  request_timeout: 15          # Decrease to 10
```

### If You Want Fewer Items
Edit [config.yaml](c:\AI_Tracker\ai-world-tracker\config.yaml):
```yaml
collector:
  reddit_count: 15    # Reduce to 10
  youtube_count: 10   # Reduce to 5
  medium_count: 10    # Reduce to 5
```

### To Disable Specific Sources
Edit [data_collector.py](c:\AI_Tracker\ai-world-tracker\data_collector.py):
Comment out the task in `_collect_all_async()`:
```python
# named_tasks.append(("Reddit", self._collect_reddit_async(session, semaphore, reddit_count)))
```

## Rollback Instructions

If you need to revert to the old version:

1. **Restore config.yaml**:
```yaml
collector:
  max_total: 100
  news_count: 25
  developer_count: 20
  community_count: 10
  # Remove: youtube_count, reddit_count, etc.
```

2. **Disable new collection methods**:
In `_collect_all_async()`, comment out lines with:
- Reddit
- Papers with Code
- YouTube
- Medium
- Bilibili
- Newsletter feeds

## Next Steps

### 1. Run Initial Collection
```powershell
python TheWorldOfAI.py
```

### 2. Review Results
Check the generated report for:
- Source diversity
- Content quality
- Item distribution

### 3. Tune Configuration
Adjust counts in config.yaml based on your preferences

### 4. Monitor Performance
Track collection times and adjust concurrency if needed

## Support

### Documentation
- [NEW_DATA_SOURCES.md](docs/NEW_DATA_SOURCES.md) - Complete source details
- [DATA_COLLECTOR_ARCHITECTURE.md](docs/DATA_COLLECTOR_ARCHITECTURE.md) - Architecture overview

### Testing
- [test_new_sources.py](tests/test_new_sources.py) - Comprehensive tests
- Run: `python tests/test_new_sources.py`

### Issues
If you encounter problems:
1. Check the console output for error messages
2. Run the test script to isolate the issue
3. Check failed sources summary
4. Review network connectivity

## Summary

✅ **No manual configuration required** - Everything is pre-configured  
✅ **Backward compatible** - Old sources still work  
✅ **Easy to customize** - Adjust config.yaml as needed  
✅ **Well tested** - Test script included  
✅ **Documented** - Full documentation available  

**Ready to use!** Just run `python TheWorldOfAI.py` to start collecting from all sources.
