# YouTube Analytics Export Guide

**Version:** 1.0
**Date:** March 24, 2026
**Purpose:** Export and analyze YouTube channel statistics for keyword optimization

---

## 📊 Quick Start: Export Analytics (No Coding Required)

### Method 1: YouTube Studio (Recommended for Getting Started)

**Step 1: Export Search Terms**
1. Go to [YouTube Studio](https://studio.youtube.com)
2. Click **Analytics** → **Reach** tab
3. Scroll to **Traffic source: YouTube search**
4. Click **"SEE MORE"**
5. Click the **download icon** (top right)
6. Save as `youtube_search_terms.csv`

**Step 2: Export Video Performance**
1. Go to **Analytics** → **Content** tab
2. Click **"SEE MORE"** next to your video list
3. Click the **download icon** (top right)
4. Select metrics:
   - Views
   - Impressions
   - Click-through rate (CTR)
   - Average view duration
   - Watch time
5. Save as `youtube_video_performance.csv`

**Step 3: Export Traffic Sources**
1. Go to **Analytics** → **Reach** tab
2. Scroll to **Traffic source types**
3. Click **"SEE MORE"**
4. Click the **download icon**
5. Save as `youtube_traffic_sources.csv`

---

## 🔍 Analyzing Your Keywords

### Compare Generated vs Actual Search Terms

Once you have `youtube_search_terms.csv` from YouTube Studio:

```bash
# Run keyword gap analysis
uv run python scripts/analyze_keyword_performance.py
```

**Output:**
- Shows which of your generated keywords are working
- Identifies high-traffic search terms you're missing
- Recommends new keywords to add based on actual user behavior

**Example output:**
```
KEYWORD PERFORMANCE ANALYSIS
============================================================
Total generated keywords: 18
Total actual searches: 127
Covered searches: 89 (70.1%)
Uncovered searches: 38
View coverage: 82.3%

Top 10 Missing Keywords (High Impact):
  1. קריאת התורה בנוסח ירושלמי (245 views)
  2. בר מצווה הכנות (189 views)
  3. לימוד טעמים (156 views)
  ...
```

### Update Keywords Based on Findings

If analysis shows missing keywords with high traffic:

```bash
# Update keyword service to include new terms
# Edit: src/services/youtube_keyword_service.py
```

Then regenerate keywords:

```bash
# Delete existing keywords
uv run python -c "from src.repositories.db import get_connection; get_connection().execute('DELETE FROM youtube_keywords')"

# Regenerate with updated strategy
uv run python scripts/populate_youtube_keywords.py

# Re-export for upload
uv run python scripts/export_youtube_keywords.py
```

---

## 🤖 Advanced: Programmatic Export via API

### Prerequisites

**1. Enable YouTube Data API:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (or create new)
3. Enable **YouTube Data API v3** and **YouTube Analytics API**
4. Create **OAuth 2.0 Client ID** credentials
5. Download as `data/youtube_client_secret.json`

**2. Install Dependencies:**
```bash
uv add google-api-python-client google-auth-oauthlib
```

### Export All Analytics

```bash
# Exports last 90 days of data:
# - Channel analytics (views, watch time, subscribers)
# - Video performance
# - Traffic sources
# - Search terms
uv run python scripts/export_youtube_analytics.py
```

**First run:** Browser will open for OAuth authorization

**Subsequent runs:** Uses saved token (`data/youtube_analytics_token.json`)

**Output files:**
- `youtube_channel_analytics.csv` - Daily channel metrics
- `youtube_video_analytics.csv` - Per-video performance
- `youtube_traffic_sources.csv` - Where viewers come from
- `youtube_search_terms.csv` - What users searched

---

## 📈 Key Metrics to Track

### For Keyword Optimization

| Metric | What It Means | How to Improve |
|--------|---------------|----------------|
| **Impressions** | How often your video appears in search/recommendations | Better titles, thumbnails, keywords |
| **CTR (Click-through rate)** | % of impressions that become views | Better titles and thumbnails |
| **Search traffic %** | Views from YouTube search | Optimize keywords and descriptions |
| **Search terms** | Actual queries users typed | Add missing keywords, adjust strategy |
| **Traffic source: External** | Views from outside YouTube | Share links, embed videos |

### For Content Performance

| Metric | What It Means | Target |
|--------|---------------|--------|
| **Average view duration** | How long people watch | >50% of video length |
| **Watch time** | Total minutes watched | Maximize (affects recommendations) |
| **Audience retention** | % who watch to end | >40% retention curve |
| **Likes/Comments ratio** | Engagement rate | >2% of views |

---

## 🎯 Keyword Optimization Workflow

### 1. Initial Setup (Done ✅)
- ✅ Generated keywords using tier strategy
- ✅ Exported to `youtube_keywords_export.csv`
- ✅ Created 494 keyword records for all videos

### 2. Monitor Performance (Weekly)

**Export search terms:**
```bash
# Manual: YouTube Studio → Analytics → Reach → YouTube search → Export
# OR
# Automated: Run API script
uv run python scripts/export_youtube_analytics.py
```

**Analyze gaps:**
```bash
uv run python scripts/analyze_keyword_performance.py
```

### 3. Optimize Keywords (Monthly)

**Identify opportunities:**
1. Review `keyword_gap_analysis.csv`
2. Find high-view search terms you're missing
3. Check if they're relevant to your content

**Update strategy:**
1. Add successful search terms to tier definitions
2. Remove low-performing keywords (if at budget limit)
3. Regenerate keywords
4. Re-upload to YouTube

### 4. A/B Test (Quarterly)

**Test different keyword approaches:**
- Try longer-tail keywords for specific parashot
- Test Hebrew vs English keyword ratios
- Experiment with seasonal keywords (holidays)

---

## 📊 Sample Analysis Queries

### Find Your Best Performing Keywords

```sql
-- Run against exported data in spreadsheet or DuckDB
SELECT
    search_term,
    views,
    views / total_views * 100 as percent_of_traffic
FROM youtube_search_terms
ORDER BY views DESC
LIMIT 20;
```

### Identify Underperforming Videos

```sql
SELECT
    video_id,
    views,
    avg_view_duration,
    CASE
        WHEN avg_view_duration < 60 THEN 'Low engagement'
        WHEN views < 50 THEN 'Low discovery'
        ELSE 'OK'
    END as issue
FROM youtube_video_analytics
WHERE issue != 'OK'
ORDER BY views DESC;
```

### Traffic Source Distribution

```sql
SELECT
    traffic_source,
    views,
    views / total_views * 100 as percent
FROM youtube_traffic_sources
ORDER BY views DESC;
```

---

## 🔧 Troubleshooting

### "Permission denied" when running API scripts

**Solution:**
1. Delete `data/youtube_analytics_token.json`
2. Re-run script to trigger OAuth flow
3. Make sure you authorize with the YouTube channel owner account

### "Quota exceeded" error

**Solution:**
- YouTube Data API has daily quota limits (10,000 units)
- Each analytics query = 1-5 units
- Reset at midnight Pacific Time
- Use manual exports for large data pulls

### Search terms show as "(not set)"

**Cause:**
- YouTube redacts search terms with <10 views (privacy)
- External traffic doesn't have search terms

**Solution:**
- Focus on terms with >10 views
- Use "Traffic source: External" report for referral URLs

---

## 📚 Additional Resources

**YouTube Studio Help:**
- [Understanding Analytics](https://support.google.com/youtube/answer/9002587)
- [Traffic Sources](https://support.google.com/youtube/answer/9314415)
- [Reach Metrics](https://support.google.com/youtube/answer/9314592)

**YouTube Data API:**
- [API Documentation](https://developers.google.com/youtube/analytics)
- [Quota Usage](https://developers.google.com/youtube/v3/getting-started#quota)
- [Python Quickstart](https://developers.google.com/youtube/analytics/quickstart/python)

**Tools:**
- [YouTube Studio](https://studio.youtube.com)
- [Google Trends](https://trends.google.com) - Search popularity
- [VidIQ](https://vidiq.com) - Third-party analytics (freemium)
- [TubeBuddy](https://www.tubebuddy.com) - Keyword research (freemium)

---

## 🎬 Next Steps

1. **Export current search terms** from YouTube Studio
2. **Run gap analysis** to find missing keywords
3. **Update your tier 4 keywords** with high-traffic terms
4. **Monitor weekly** to track improvements
5. **Iterate monthly** based on data

**Goal:** Increase search traffic from current ~35% character usage to 75% by adding proven, high-traffic keywords while maintaining relevance.

---

**END OF GUIDE**
