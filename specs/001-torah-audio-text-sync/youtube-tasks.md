# Implementation Tasks: YouTube Video Update & Playlist Management

**Feature**: YouTube video content updates, CIFRIA attribution, and playlist organization
**Generated**: 2026-03-08
**Based on**: youtube-update-playlist-management.md

---

## User Stories (Derived from Plan)

### User Story 1 (P1): Download and Preserve Thumbnails
**As a** content creator
**I want to** download and preserve existing thumbnails from the source YouTube channel
**So that** I can maintain consistent branding when updating videos

**Independent Test**: Can scan source channel, download all thumbnails, cache them locally, and verify all images are accessible.

---

### User Story 2 (P2): Upload Videos with Thumbnail Restoration
**As a** content creator
**I want to** upload new synchronized videos to YouTube while restoring the original thumbnails
**So that** viewers have a consistent visual experience

**Independent Test**: Can upload a new video, restore its original thumbnail, and verify the video is accessible on YouTube with correct thumbnail.

---

### User Story 3 (P3): Organize Videos into Parasha Playlists
**As a** content creator
**I want to** organize videos into playlists by parasha (with 7 aliyot each)
**So that** viewers can easily find and watch complete Torah portions

**Independent Test**: Can create a parasha playlist, add 7 videos in aliyah order, and verify playlist is publicly accessible with correct ordering.

---

### User Story 4 (P4): Update Video Metadata with CIFRIA Attribution
**As a** content creator
**I want to** update video metadata with CIFRIA attribution
**So that** proper credit is given to source materials

**Independent Test**: Can update video title, description, and tags with CIFRIA attribution templates and verify metadata is visible on YouTube.

---

### User Story 5 (P5): Batch Process Multiple Videos
**As a** content creator
**I want to** batch process multiple videos efficiently
**So that** I can update an entire channel without manual intervention

**Independent Test**: Can process a mapping file with 10+ videos, track progress, handle failures gracefully, and report completion status.

---

## Implementation Phases

### Phase 1: Setup & Dependencies

**Goal**: Initialize YouTube integration infrastructure and dependencies

**DuckDB Integration**: YouTube data will be stored in DuckDB (data/torah_sync.duckdb) following the existing repository pattern, rather than JSON files.

- [x] T001 Add Google YouTube API dependencies to pyproject.toml (google-api-python-client>=2.100.0, google-auth-oauthlib>=1.2.0, google-auth-httplib2>=0.2.0) ✅ COMPLETED
- [ ] T002 Add YouTube configuration section to settings.toml (client_secrets_path, token_path, source_channel, default_privacy, cifria attribution)
- [ ] T003 Create config/youtube_templates.toml with CIFRIA attribution templates (metadata.default, metadata.cifria, metadata.title_format, metadata.description_format, metadata.tags)
- [ ] T004 Create data/thumbnails/ directory structure for thumbnail image cache (images only, metadata in DuckDB)
- [ ] T005 Add YouTube DuckDB schema to src/repositories/db.py (youtube_thumbnails, youtube_uploads, youtube_playlist_meta tables with sequences and indexes)
- [ ] T006 Add .gitignore entries for client_secrets.json and youtube_token.pickle
- [ ] T007 Create config/ directory if it doesn't exist

---

### Phase 2: Foundational - Core Models & Repositories

**Goal**: Create data models and repository classes for YouTube entities (blocking prerequisite for all user stories)

**DuckDB Integration**: All models have corresponding repository classes that interact with DuckDB tables.

**Models**:
- [ ] T008 Create src/models/youtube_video.py with YouTubeVideo model (video_id, title, description, thumbnail_url, thumbnail_local_path, published_at, duration, view_count, privacy_status, alya_video_id for FK)
- [ ] T009 Create src/models/video_mapping.py with VideoMapping model (youtube_video_id, new_video_path, alya_id for FK, preserve_thumbnail, preserve_metadata, validate_new_video_exists())
- [ ] T010 Create src/models/youtube_metadata.py with YouTubeMetadata model (video_id, title, description, tags, category_id, default_language, privacy_status, cifria_attribution)
- [ ] T011 Create src/models/youtube_playlist.py with YouTubePlaylist model (playlist_id FK, youtube_playlist_id, title, description, privacy_status, video_ids, aliyah_count, is_complete(), get_aliyah_position())
- [ ] T012 Create src/models/youtube_thumbnail.py with YouTubeThumbnail model (id, video_id, original_url, cached_path, title, downloaded_at)
- [ ] T013 Create src/models/youtube_upload.py with YouTubeUpload model (id, alya_video_id FK, old_youtube_video_id, new_youtube_video_id, thumbnail_restored, added_to_playlist, upload_status, uploaded_at)

**Repositories**:
- [ ] T014 [P] Create src/repositories/youtube_thumbnail_repo.py with YouTubeThumbnailRepository (save_thumbnail(), get_by_video_id(), list_all())
- [ ] T015 [P] Create src/repositories/youtube_upload_repo.py with YouTubeUploadRepository (create_upload(), update_status(), get_by_alya_video(), list_pending())
- [ ] T016 [P] Create src/repositories/youtube_playlist_meta_repo.py with YouTubePlaylistMetaRepository (create_meta(), get_by_playlist(), update_video_count(), is_complete())

**Auth**:
- [ ] T017 [P] Create src/services/youtube/auth.py with YouTubeAuth class (OAuth2 flow, get_credentials(), token refresh, pickle-based storage)

---

### Phase 3: User Story 1 - Download and Preserve Thumbnails

**Goal**: Scan source channel and download all thumbnails for caching

**Independent Test Criteria**:
- ✓ Can authenticate with YouTube API using OAuth2
- ✓ Can resolve channel handle to channel ID
- ✓ Can list all videos from source channel
- ✓ Can download thumbnails to local cache
- ✓ Thumbnails are accessible after download

**Tasks**:

- [ ] T018 [P] [US1] Create src/services/youtube/channel_scanner.py with ChannelScanner class (get_channel_id_from_handle(), list_all_videos())
- [ ] T019 [US1] Implement ChannelScanner.get_channel_id_from_handle() method to resolve @קריאהבתורהמפייוסףבודנהיימר to channel ID
- [ ] T020 [US1] Implement ChannelScanner.list_all_videos() method with pagination support (maxResults=50, nextPageToken handling)
- [ ] T021 [P] [US1] Create src/services/youtube/thumbnail_manager.py with ThumbnailManager class using YouTubeThumbnailRepository (download_thumbnail(), download_all_thumbnails(), get_cached_thumbnail())
- [ ] T022 [US1] Implement ThumbnailManager.download_thumbnail() with httpx for downloading images, save to data/thumbnails/, persist metadata to DuckDB via repository
- [ ] T023 [US1] Implement ThumbnailManager.download_all_thumbnails() for batch thumbnail download with error handling and DuckDB batch inserts
- [ ] T024 [US1] Implement ThumbnailManager.get_cached_thumbnail() to query DuckDB and verify file exists
- [ ] T025 [P] [US1] Create src/cli/youtube_commands.py with youtube CLI group and prepare-channel command
- [ ] T026 [US1] Implement prepare-channel CLI command (channel handle input, progress display, success/failure reporting, DuckDB transaction)
- [ ] T027 [US1] Implement list-videos CLI command to export channel videos from DuckDB query (video_id, title, published_at, thumbnail_url)

---

### Phase 4: User Story 2 - Upload Videos with Thumbnail Restoration

**Goal**: Upload new videos and restore original thumbnails

**Independent Test Criteria**:
- ✓ Can upload a video file to YouTube via API
- ✓ Can set video metadata during upload
- ✓ Can restore cached thumbnail after upload
- ✓ Video is playable on YouTube with correct thumbnail

**Tasks**:

- [ ] T022 [P] [US2] Create src/services/youtube/video_updater.py with VideoUpdater class (update_video(), _upload_new_video(), _restore_thumbnail(), _build_default_metadata())
- [ ] T023 [US2] Implement VideoUpdater._upload_new_video() with MediaFileUpload and resumable uploads (10MB chunks, progress tracking)
- [ ] T024 [US2] Implement VideoUpdater._restore_thumbnail() using thumbnails().set() API endpoint
- [ ] T025 [US2] Implement VideoUpdater._build_default_metadata() to construct title/description from VideoMapping
- [ ] T026 [US2] Implement VideoUpdater.update_video() orchestration (validate file exists, check cached thumbnail, upload video, restore thumbnail, return result dict)
- [ ] T027 [US2] Add error handling for upload failures (HTTPError, network issues, invalid video format)
- [ ] T028 [P] [US2] Create src/services/youtube/metadata_builder.py with MetadataBuilder class (build(), _build_title(), _build_description(), _build_tags())
- [ ] T029 [US2] Implement MetadataBuilder._build_title() using youtube_templates.toml pattern ("{parasha} - {aliyah} - {tradition} | CIFRIA", max 100 chars)
- [ ] T030 [US2] Implement MetadataBuilder._build_description() with CIFRIA attribution (cifria_attribution, cifria_website, cifria_acknowledgment)
- [ ] T031 [US2] Implement MetadataBuilder._build_tags() combining default tags with parasha/aliyah names (max 500 chars total)
- [ ] T032 [US2] Implement update-video CLI command (video_id, new_video_path, parasha, aliyah, tradition flags, success/failure reporting)

---

### Phase 5: User Story 3 - Organize Videos into Parasha Playlists

**Goal**: Create and manage playlists for each parasha with 7 aliyot

**Independent Test Criteria**:
- ✓ Can create a new playlist with CIFRIA branding
- ✓ Can get-or-create playlist (check cache first)
- ✓ Can add videos to playlist at specific positions
- ✓ Can add videos by aliyah name (ראשון → position 0, שני → position 1, etc.)
- ✓ Playlist is publicly accessible with correct video ordering

**Tasks**:

- [ ] T033 [P] [US3] Create src/services/youtube/playlist_manager.py with PlaylistManager class (create_playlist(), get_or_create_playlist(), add_video_to_playlist(), add_video_by_aliyah(), list_all_playlists())
- [ ] T034 [US3] Implement PlaylistManager.create_playlist() with playlists().insert() API (snippet.title, snippet.description, status.privacyStatus)
- [ ] T035 [US3] Implement PlaylistManager playlist caching to data/playlists/parasha_playlists.json (playlist_id, title, created_at, tradition)
- [ ] T036 [US3] Implement PlaylistManager.get_or_create_playlist() with cache-first lookup and fallback to creation
- [ ] T037 [US3] Implement PlaylistManager.get_playlist() to fetch playlist details and video IDs via playlistItems().list()
- [ ] T038 [US3] Implement PlaylistManager._get_playlist_video_ids() with pagination (maxResults=50, nextPageToken)
- [ ] T039 [US3] Implement PlaylistManager.add_video_to_playlist() using playlistItems().insert() with position parameter
- [ ] T040 [US3] Implement PlaylistManager.add_video_by_aliyah() mapping Hebrew aliyah names to positions (ראשון:0, שני:1, שלישי:2, רביעי:3, חמישי:4, ששי:5, שביעי:6)
- [ ] T041 [US3] Implement PlaylistManager.list_all_playlists() using playlists().list(mine=True) with pagination
- [ ] T042 [US3] Integrate PlaylistManager into VideoUpdater.update_video() (add video to playlist after upload, playlist_added flag in result)
- [ ] T043 [US3] Implement create-playlist CLI command (parasha_name, tradition flag, playlist ID output)
- [ ] T044 [US3] Implement list-playlists CLI command (display all playlists with completion status: ✓/○, video count X/7)
- [ ] T045 [US3] Implement add-to-playlist CLI command (playlist_id, video_id, optional position flag)

---

### Phase 6: User Story 4 - Update Video Metadata with CIFRIA Attribution

**Goal**: Apply CIFRIA attribution templates to video metadata

**Independent Test Criteria**:
- ✓ Can update existing video metadata via API
- ✓ CIFRIA attribution appears in title
- ✓ CIFRIA attribution appears in description with website and acknowledgment
- ✓ Default tags include "CIFRIA"
- ✓ Metadata visible on YouTube matches templates

**Tasks**:

- [ ] T046 [P] [US4] Create src/services/youtube/api_client.py with YouTubeAPIClient class (update_metadata(), upload_thumbnail(), get_video_details())
- [ ] T047 [US4] Implement YouTubeAPIClient.update_metadata() using videos().update() API (snippet, status parts)
- [ ] T048 [US4] Implement YouTubeAPIClient.upload_thumbnail() using thumbnails().set() with MediaFileUpload
- [ ] T049 [US4] Implement YouTubeAPIClient.get_video_details() using videos().list() API (snippet, status, contentDetails parts)
- [ ] T050 [US4] Add CIFRIA attribution validation to MetadataBuilder (ensure attribution_text present in description)
- [ ] T051 [US4] Update MetadataBuilder to use dynaconf for template loading (metadata.cifria.attribution_text, metadata.cifria.website, metadata.cifria.acknowledgment)
- [ ] T052 [US4] Create example config/video_mappings.json with sample parasha/aliyah mappings (youtube_video_id, new_video_path, parasha_name, aliyah_name, tradition)

---

### Phase 7: User Story 5 - Batch Process Multiple Videos

**Goal**: Process multiple videos from mapping file with progress tracking

**Independent Test Criteria**:
- ✓ Can load video mappings from JSON file
- ✓ Can process each mapping sequentially
- ✓ Progress is displayed during batch processing (X/Y complete)
- ✓ Failures are logged and don't stop batch
- ✓ Final report shows success/failure counts
- ✓ Failed videos are listed with error messages

**Tasks**:

- [ ] T053 [P] [US5] Create src/services/youtube/update_workflow.py with YouTubeUpdateWorkflow class (prepare_channel(), update_single_video(), update_batch())
- [ ] T054 [US5] Implement YouTubeUpdateWorkflow.__init__() initializing ChannelScanner, ThumbnailManager, PlaylistManager, VideoUpdater
- [ ] T055 [US5] Implement YouTubeUpdateWorkflow.prepare_channel() orchestrating channel ID resolution, video listing, thumbnail download
- [ ] T056 [US5] Implement YouTubeUpdateWorkflow.update_single_video() wrapping VideoUpdater.update_video() with optional metadata builder
- [ ] T057 [US5] Implement YouTubeUpdateWorkflow.update_batch() with loop over mappings, try/catch per video, results collection
- [ ] T058 [US5] Add batch progress logging in update_batch() ("Processing video X/Y", "Successfully updated video", "Failed to update video")
- [ ] T059 [US5] Implement batch-update CLI command (mappings_file input, progress display, success/failure summary, failed videos list)
- [ ] T060 [US5] Add batch error handling (continue on individual failures, collect errors, report at end)

---

### Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Documentation, error handling, and production readiness

- [ ] T061 [P] Create OAuth2 setup guide in docs/youtube-oauth-setup.md (Google Cloud project, enable API, create credentials, download client_secrets.json)
- [ ] T062 [P] Update README.md with YouTube workflow section (prepare-channel, update-video, create-playlist, batch-update examples)
- [ ] T063 [P] Create example .secrets.toml.example for YouTube configuration (client_secrets_path, default_privacy, source_channel)
- [ ] T064 Add API quota monitoring (log API calls, track quota usage, warn at 80% threshold)
- [ ] T065 Add retry logic with exponential backoff for transient API errors (HttpError 500/503, network timeouts)
- [ ] T066 [P] Add logging consistency across all YouTube services (logger.debug for API calls with f"{var=}", logger.info for milestones, logger.error for failures)
- [ ] T067 Create troubleshooting guide in docs/youtube-troubleshooting.md (OAuth errors, quota exceeded, thumbnail upload failures, playlist issues)
- [ ] T068 Add validation for video file formats (accept mp4, reject others with clear error)
- [ ] T069 Add validation for parasha/aliyah names (check against known values, provide suggestions for typos)
- [ ] T070 Create example usage scripts in examples/youtube/ (prepare_haazinu.sh, update_single_video.sh, batch_update_all.sh)

---

## Dependencies & Execution Order

### Story Completion Order (MVP → Full Feature)

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational - Core Models)
    ↓
├─→ US1: Download Thumbnails (Phase 3)
│       ↓
├─→ US2: Upload Videos (Phase 4) ──→ Requires US1 thumbnails
│       ↓
├─→ US3: Playlist Management (Phase 5) ── Can run in parallel with US2
│       ↓
├─→ US4: Metadata with CIFRIA (Phase 6) ── Integrates with US2
│       ↓
└─→ US5: Batch Processing (Phase 7) ──→ Requires US1-US4 complete
        ↓
    Phase 8 (Polish)
```

**Critical Path**: Setup → Core Models → US1 → US2 → US5
**Parallel Opportunities**: US3 (playlists) can be developed independently after Core Models

---

## Parallel Execution Examples

### Phase 3 (US1) - Download Thumbnails
**Parallelizable tasks**: T012 (ChannelScanner), T015 (ThumbnailManager), T019 (CLI setup)
**Blocking task**: T020 (prepare-channel command requires both scanner and manager)

### Phase 4 (US2) - Upload Videos
**Parallelizable tasks**: T022 (VideoUpdater), T028 (MetadataBuilder)
**Blocking task**: T026 (update_video orchestration requires both components)

### Phase 5 (US3) - Playlists
**Parallelizable tasks**: All T033-T040 can proceed independently
**Blocking task**: T042 (integration requires VideoUpdater from Phase 4)

### Phase 6 (US4) - Metadata
**Parallelizable tasks**: T046 (APIClient), T050 (validation), T052 (examples)
**Blocking task**: T047 (update_metadata requires APIClient)

### Phase 7 (US5) - Batch Processing
**Parallelizable tasks**: T053 (Workflow setup), T059 (CLI command)
**Blocking tasks**: T057 (update_batch requires all previous US implementations)

### Phase 8 - Polish
**All parallelizable**: Documentation tasks (T061-T063, T067, T070) can proceed independently

---

## MVP Scope Recommendation

**Minimum Viable Product (MVP)**: Phases 1-4 (Setup → Core Models → US1 → US2)

**Rationale**:
- Phase 1-2: Infrastructure required for any YouTube operation
- US1 (Phase 3): Thumbnail preservation is core requirement
- US2 (Phase 4): Video upload with thumbnail is primary user value

**Deferred for v2**:
- US3 (Playlists): Nice-to-have organization feature
- US4 (Advanced Metadata): Basic metadata works, CIFRIA attribution can be enhanced later
- US5 (Batch Processing): Manual processing acceptable for MVP

**MVP Deliverable**: CLI tool that can:
1. Download thumbnails from source channel
2. Upload a new video file
3. Restore the original thumbnail
4. Set basic metadata

---

## Task Validation Checklist

✅ All tasks follow format: `- [ ] [TID] [P?] [Story?] Description with file path`
✅ Each user story has independent test criteria
✅ Tasks organized by user story phases
✅ Dependencies clearly documented
✅ Parallel opportunities identified
✅ MVP scope defined (Phases 1-4)
✅ File paths specified for all implementation tasks
✅ Setup phase has no story labels
✅ Foundational phase has no story labels
✅ User story phases have [US#] labels
✅ Polish phase has no story labels

---

## Summary

**Total Tasks**: 70
**Setup Phase**: 6 tasks
**Foundational Phase**: 5 tasks
**User Story 1 (Download Thumbnails)**: 10 tasks
**User Story 2 (Upload Videos)**: 11 tasks
**User Story 3 (Playlists)**: 13 tasks
**User Story 4 (Metadata)**: 7 tasks
**User Story 5 (Batch Processing)**: 8 tasks
**Polish Phase**: 10 tasks

**Parallel Opportunities**: 15 tasks marked [P]
**Independent Test Criteria**: 5 user stories with testable acceptance criteria
**Estimated MVP Duration**: ~8-10 days (Phases 1-4)
**Estimated Full Feature Duration**: ~16-20 days (All phases)

---

## Next Steps

1. **Start with MVP**: Execute T001-T032 (Phases 1-4)
2. **Create test account**: Set up YouTube test channel for integration testing
3. **Obtain OAuth credentials**: Follow docs/youtube-oauth-setup.md
4. **Test with פרשת האזינו**: Use as pilot parasha for validation
5. **Iterate**: Gather feedback before implementing Phases 5-8
