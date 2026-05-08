import React, { useEffect, useState, useCallback } from "react";
import {
  Home, BookOpen, ExternalLink, ChevronDown, ChevronUp,
  Loader2, Bookmark, BookmarkCheck, Trash2
} from "lucide-react";
import api from "../services/api";
import ThemeToggle from "../components/ThemeToggle";
import TopicIcon, { getTopicColors } from "../components/TopicIcon";

const PER_TOPIC = 3;
const TAB_RECOMMENDED = "recommended";
const TAB_BOOKMARKS   = "bookmarks";

export default function LearningMaterials({ user, onBack, onOpenResource }) {
  const [tab, setTab] = useState(TAB_RECOMMENDED);

  // ── Recommended tab ────────────────────────────────────────────────────────
  const [loading, setLoading]   = useState(true);
  const [topics, setTopics]     = useState([]);
  const [error, setError]       = useState("");
  const [apiUser, setApiUser]   = useState(null);
  // per-topic pagination: { [topicName]: { pages: [[...resources]], currentPageIdx, hasMore } }
  const [topicPagination, setTopicPagination] = useState({});
  const [loadingMore, setLoadingMore] = useState({});

  // ── Bookmarks tab ──────────────────────────────────────────────────────────
  const [bookmarks, setBookmarks]           = useState([]);
  const [bookmarksLoading, setBookmarksLoading] = useState(false);

  // ── Load initial recommendations ───────────────────────────────────────────
  const loadInitial = useCallback(async () => {
    if (!user?.id) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.get(`/recommender/topics/${user.id}`, {
        params: { page: 1, per_topic: PER_TOPIC },
      });
      setApiUser(res.data.user || null);
      const incoming = res.data.topics || [];
      setTopics(incoming);

      // Initialise pagination state for each topic
      const pag = {};
      for (const t of incoming) {
        pag[t.topic] = {
          pages: [t.resources],   // page index 0 = first page
          currentPageIdx: 0,
          hasMore: t.has_more,
          serverPage: 1,          // which server page we last fetched
        };
      }
      setTopicPagination(pag);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  useEffect(() => { loadInitial(); }, [loadInitial]);

  // ── Fetch next page for a topic and append ─────────────────────────────────
  const loadMoreForTopic = async (topicName) => {
    setLoadingMore((prev) => ({ ...prev, [topicName]: true }));
    try {
      const pag = topicPagination[topicName];
      const nextServerPage = (pag?.serverPage || 1) + 1;
      const res = await api.get(`/recommender/topics/${user.id}`, {
        params: { page: nextServerPage, per_topic: PER_TOPIC },
      });
      const freshTopic = (res.data.topics || []).find((t) => t.topic === topicName);
      if (freshTopic) {
        setTopicPagination((prev) => {
          const existing = prev[topicName];
          const newPages = [...existing.pages, freshTopic.resources];
          return {
            ...prev,
            [topicName]: {
              pages: newPages,
              currentPageIdx: newPages.length - 1,  // jump to new page
              hasMore: freshTopic.has_more,
              serverPage: nextServerPage,
            },
          };
        });
      }
    } catch (err) {
      console.error("Load more error:", err);
    } finally {
      setLoadingMore((prev) => ({ ...prev, [topicName]: false }));
    }
  };

  // ── Navigate pages locally (prev / next without refetch) ──────────────────
  const goToPrevPage = (topicName) => {
    setTopicPagination((prev) => {
      const pag = prev[topicName];
      if (!pag || pag.currentPageIdx <= 0) return prev;
      return { ...prev, [topicName]: { ...pag, currentPageIdx: pag.currentPageIdx - 1 } };
    });
  };

  const goToNextPage = (topicName) => {
    setTopicPagination((prev) => {
      const pag = prev[topicName];
      if (!pag) return prev;
      const nextIdx = pag.currentPageIdx + 1;
      if (nextIdx < pag.pages.length) {
        // already fetched — just navigate
        return { ...prev, [topicName]: { ...pag, currentPageIdx: nextIdx } };
      }
      return prev; // will trigger loadMoreForTopic instead
    });
  };

  // ── Bookmarks ──────────────────────────────────────────────────────────────
  const loadBookmarks = useCallback(async () => {
    if (!user?.id) return;
    setBookmarksLoading(true);
    try {
      const res = await api.get(`/recommender/bookmarks/${user.id}`);
      setBookmarks(res.data.items || []);
    } catch {}
    finally { setBookmarksLoading(false); }
  }, [user?.id]);

  const removeBookmark = async (resourceId) => {
    try {
      await api.post("/recommender/bookmark", {
        user_id: user.id,
        resource_id: resourceId,
        bookmarked: false,
      });
      setBookmarks((prev) => prev.filter((r) => r.id !== resourceId));
    } catch {}
  };

  const handleTabChange = (newTab) => {
    setTab(newTab);
    if (newTab === TAB_BOOKMARKS) loadBookmarks();
  };

  const style = apiUser?.learning_style || user?.varkResult?.learning_style || user?.learning_style || "Not set";
  const level = apiUser?.level || user?.level || "Not set";

  const tabBase = "px-4 py-2 rounded-xl text-sm font-medium transition-colors";
  const tabActive = "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20";
  const tabInactive = "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700";

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white p-6 transition-colors">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <div className="flex justify-between items-center mb-6 flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-cyan-600 dark:text-cyan-400" />
            <div>
              <h1 className="text-2xl font-bold">Learning Materials</h1>
              <p className="text-gray-500 dark:text-slate-400 text-sm">Personalised resources grouped by topic</p>
            </div>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <ThemeToggle />
            <button onClick={onBack}
              className="flex items-center gap-2 px-4 py-2 rounded-xl transition-colors bg-white hover:bg-gray-100 border border-gray-200 text-gray-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300">
              <Home className="w-4 h-4" /> Dashboard
            </button>
          </div>
        </div>

        {/* User badges */}
        <div className="mb-5 p-4 rounded-xl bg-gray-50 border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 flex gap-6 flex-wrap transition-colors">
          <p className="text-gray-700 dark:text-slate-300">
            Learning Style: <span className="font-semibold text-cyan-600 dark:text-cyan-400">{style}</span>
          </p>
          <p className="text-gray-700 dark:text-slate-300">
            Level: <span className="font-semibold text-cyan-600 dark:text-cyan-400">{level}</span>
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button className={`${tabBase} ${tab === TAB_RECOMMENDED ? tabActive : tabInactive}`}
            onClick={() => handleTabChange(TAB_RECOMMENDED)}>
            <span className="flex items-center gap-1.5"><BookOpen className="w-4 h-4" /> Recommended</span>
          </button>
          <button className={`${tabBase} ${tab === TAB_BOOKMARKS ? tabActive : tabInactive}`}
            onClick={() => handleTabChange(TAB_BOOKMARKS)}>
            <span className="flex items-center gap-1.5"><Bookmark className="w-4 h-4" /> Saved</span>
          </button>
        </div>

        {/* ── RECOMMENDED TAB ───────────────────────────────────────────────── */}
        {tab === TAB_RECOMMENDED && (
          <>
            {loading && (
              <div className="flex items-center gap-2 text-gray-500 dark:text-slate-400">
                <Loader2 className="w-4 h-4 animate-spin" /> Loading recommendations…
              </div>
            )}
            {error && <p className="text-red-600 dark:text-red-400">{error}</p>}
            {!loading && !error && topics.length === 0 && (
              <div className="p-6 rounded-xl bg-gray-50 border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 transition-colors">
                <p>No matching materials found yet.</p>
              </div>
            )}

            <div className="space-y-10">
              {topics.map((topicGroup) => {
                const colors = getTopicColors(topicGroup.topic);
                const pag = topicPagination[topicGroup.topic];
                const currentResources = pag ? pag.pages[pag.currentPageIdx] : topicGroup.resources;
                const isLoadingMore = loadingMore[topicGroup.topic];
                const canGoPrev = pag && pag.currentPageIdx > 0;
                // can go next = there's a fetched page ahead OR server has more
                const hasFetchedNext = pag && pag.currentPageIdx < pag.pages.length - 1;
                const canGoNext = hasFetchedNext || (pag && pag.hasMore);
                const pageLabel = pag ? `Page ${pag.currentPageIdx + 1}` : "";

                return (
                  <section key={topicGroup.topic}>
                    <div className="flex items-center gap-3 mb-4">
                      <TopicIcon topic={topicGroup.topic} size={36} />
                      <div>
                        <h2 className="text-lg font-bold" style={{ color: colors.fg }}>
                          {topicGroup.pretty_topic || topicGroup.topic}
                        </h2>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {(currentResources || []).map((r) => (
                        <ResourceCard key={r.id} resource={r} onOpen={onOpenResource} />
                      ))}
                    </div>

                    {/* Prev / Next pagination row */}
                    {(canGoPrev || canGoNext) && (
                      <div className="mt-4 flex items-center justify-center gap-3">
                        <button
                          onClick={() => goToPrevPage(topicGroup.topic)}
                          disabled={!canGoPrev}
                          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-colors
                                     bg-gray-100 hover:bg-gray-200 text-gray-700
                                     dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300
                                     disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          <ChevronUp className="w-4 h-4 rotate-[-90deg]" /> Previous
                        </button>

                        <span className="text-xs text-gray-400 dark:text-slate-500 min-w-[60px] text-center">
                          {pageLabel}
                        </span>

                        <button
                          onClick={() => {
                            if (hasFetchedNext) {
                              goToNextPage(topicGroup.topic);
                            } else {
                              loadMoreForTopic(topicGroup.topic);
                            }
                          }}
                          disabled={!canGoNext || isLoadingMore}
                          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-colors
                                     bg-gray-100 hover:bg-gray-200 text-gray-700
                                     dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300
                                     disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          {isLoadingMore
                            ? <><Loader2 className="w-4 h-4 animate-spin" /> Loading…</>
                            : <>Next <ChevronDown className="w-4 h-4 rotate-[-90deg]" /></>
                          }
                        </button>
                      </div>
                    )}
                  </section>
                );
              })}
            </div>
          </>
        )}

        {/* ── BOOKMARKS TAB ─────────────────────────────────────────────────── */}
        {tab === TAB_BOOKMARKS && (
          <>
            {bookmarksLoading && (
              <div className="flex items-center gap-2 text-gray-500 dark:text-slate-400">
                <Loader2 className="w-4 h-4 animate-spin" /> Loading saved resources…
              </div>
            )}
            {!bookmarksLoading && bookmarks.length === 0 && (
              <div className="p-6 rounded-xl bg-gray-50 border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 text-center">
                <BookmarkCheck className="w-8 h-8 mx-auto mb-2 text-gray-300 dark:text-slate-600" />
                <p className="text-gray-500 dark:text-slate-400">
                  No saved resources yet. Tap the <strong>Save</strong> button on any resource to bookmark it.
                </p>
              </div>
            )}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {bookmarks.map((r) => (
                <ResourceCard
                  key={r.id}
                  resource={r}
                  onOpen={onOpenResource}
                  actionOverride={
                    <div className="mt-auto flex gap-2 flex-wrap">
                      <button
                        onClick={() => onOpenResource(r)}
                        className="inline-flex items-center gap-2 px-3 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-white rounded-xl transition text-xs shadow-lg shadow-cyan-500/20"
                      >
                        Open <ExternalLink className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => removeBookmark(r.id)}
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 dark:text-red-400 dark:bg-red-500/10 dark:hover:bg-red-500/20 dark:border-red-500/30 transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" /> Remove
                      </button>
                    </div>
                  }
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ResourceCard({ resource: r, onOpen, actionOverride }) {
  const colors = getTopicColors(r.topic);
  const prettyTopic = r.topic ? r.topic.replace(/_/g, " ") : "";

  return (
    <div className="bg-white border border-gray-200 shadow-sm dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-5 flex flex-col transition-colors">
      <div className="flex gap-3 items-start mb-3">
        <TopicIcon topic={r.topic} size={40} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium mb-1 truncate" style={{ color: colors.fg }}>
            {prettyTopic}{r.subtopic ? ` • ${r.subtopic}` : ""}
          </p>
          <h3 className="text-base font-bold text-gray-900 dark:text-white leading-snug line-clamp-2">
            {r.title}
          </h3>
        </div>
      </div>

      <p className="text-gray-400 dark:text-slate-500 text-xs mb-2">
        {[r.resource_type, r.difficulty, r.vark_style, r.duration_minutes && `${r.duration_minutes} min`]
          .filter(Boolean)
          .join(" • ")}
      </p>

      {r.description && (
        <p className="text-gray-600 dark:text-slate-300 text-sm mb-4 line-clamp-3 flex-1">
          {r.description}
        </p>
      )}

      {actionOverride || (
        <button
          onClick={() => onOpen(r)}
          className="mt-auto inline-flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-white rounded-xl transition text-sm shadow-lg shadow-cyan-500/20 self-start"
        >
          Open Resource <ExternalLink className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
