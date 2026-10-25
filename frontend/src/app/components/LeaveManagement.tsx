import { useState } from "react";
import { Calendar, Check, X, Clock, User } from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsList, TabsTrigger } from "./ui/tabs";
import { leaveRequests } from "../data/mockData";

const typeColors: Record<string, string> = {
  Annual: "bg-blue-50 text-blue-700 border-blue-200",
  Sick: "bg-red-50 text-red-700 border-red-200",
  Personal: "bg-purple-50 text-purple-700 border-purple-200",
  Unpaid: "bg-gray-50 text-gray-700 border-gray-200",
};

const statusColors: Record<string, string> = {
  Pending: "bg-amber-100 text-amber-700 hover:bg-amber-100",
  Approved: "bg-green-100 text-green-700 hover:bg-green-100",
  Rejected: "bg-red-100 text-red-700 hover:bg-red-100",
};

export function LeaveManagement() {
  const [requests, setRequests] = useState(leaveRequests);
  const [activeTab, setActiveTab] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(leaveRequests[0]?.id ?? null);

  const handleApprove = (id: string) => {
    setRequests((prev) =>
      prev.map((req) => (req.id === id ? { ...req, status: "Approved" as const } : req))
    );
  };

  const handleReject = (id: string) => {
    setRequests((prev) =>
      prev.map((req) => (req.id === id ? { ...req, status: "Rejected" as const } : req))
    );
  };

  const filteredRequests =
    activeTab === "all"
      ? requests
      : requests.filter((req) => req.status.toLowerCase() === activeTab);

  const pendingCount = requests.filter((req) => req.status === "Pending").length;
  const selected = requests.find((r) => r.id === selectedId);

  return (
    <div className="flex h-full">
      {/* Left panel: list */}
      <div className="w-96 flex-shrink-0 flex flex-col border-r border-gray-200 bg-white">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-200">
          <h1 className="text-lg font-semibold text-gray-900 mb-4">Leave Management</h1>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="w-full grid grid-cols-3">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="pending">
                Pending {pendingCount > 0 && `(${pendingCount})`}
              </TabsTrigger>
              <TabsTrigger value="approved">Approved</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {filteredRequests.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <Calendar className="w-10 h-10 mx-auto mb-3 opacity-40" />
              <p className="text-sm">No requests found</p>
            </div>
          ) : (
            filteredRequests.map((leave) => (
              <button
                key={leave.id}
                onClick={() => setSelectedId(leave.id)}
                className={`w-full text-left px-6 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                  selectedId === leave.id ? "bg-blue-50 border-l-2 border-l-blue-500" : ""
                }`}
              >
                <div className="flex items-start justify-between mb-1.5">
                  <p className="text-sm font-semibold text-gray-900">{leave.staffName}</p>
                  <Badge className={statusColors[leave.status]}>{leave.status}</Badge>
                </div>
                <p className="text-xs text-gray-500 mb-1.5">{leave.staffRole}</p>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={`text-xs ${typeColors[leave.type]}`}>
                    {leave.type}
                  </Badge>
                  <span className="text-xs text-gray-400">{leave.days} days</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Right panel: detail */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {selected ? (
          <div className="p-8 max-w-2xl">
            {/* Staff header */}
            <div className="flex items-start gap-4 mb-8">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center text-white text-lg font-bold flex-shrink-0">
                {selected.staffName.split(" ").map((n) => n[0]).join("")}
              </div>
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">{selected.staffName}</h2>
                    <p className="text-sm text-gray-500 mt-0.5">{selected.staffRole}</p>
                  </div>
                  <Badge className={`text-sm ${statusColors[selected.status]}`}>
                    {selected.status}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Info grid */}
            <div className="grid grid-cols-2 gap-5 mb-6">
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 text-gray-500 mb-2">
                    <Calendar className="w-4 h-4" />
                    <span className="text-xs font-medium uppercase tracking-wide">Leave Type</span>
                  </div>
                  <Badge variant="outline" className={typeColors[selected.type]}>
                    {selected.type} Leave
                  </Badge>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 text-gray-500 mb-2">
                    <Clock className="w-4 h-4" />
                    <span className="text-xs font-medium uppercase tracking-wide">Duration</span>
                  </div>
                  <p className="text-lg font-bold text-gray-900">
                    {selected.days} {selected.days === 1 ? "day" : "days"}
                  </p>
                </CardContent>
              </Card>

              <Card className="col-span-2">
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 text-gray-500 mb-3">
                    <Calendar className="w-4 h-4" />
                    <span className="text-xs font-medium uppercase tracking-wide">Leave Dates</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1 bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-400 mb-1">From</p>
                      <p className="font-semibold text-gray-900">
                        {new Date(selected.startDate).toLocaleDateString("en-US", {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </p>
                    </div>
                    <div className="text-gray-300 font-light text-xl">→</div>
                    <div className="flex-1 bg-gray-50 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-400 mb-1">To</p>
                      <p className="font-semibold text-gray-900">
                        {new Date(selected.endDate).toLocaleDateString("en-US", {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Reason */}
            <Card className="mb-6">
              <CardContent className="p-5">
                <div className="flex items-center gap-2 text-gray-500 mb-2">
                  <User className="w-4 h-4" />
                  <span className="text-xs font-medium uppercase tracking-wide">Reason</span>
                </div>
                <p className="text-sm text-gray-700">{selected.reason}</p>
              </CardContent>
            </Card>

            {/* Meta */}
            <p className="text-xs text-gray-400 mb-6">
              Requested on{" "}
              {new Date(selected.requestedDate).toLocaleDateString("en-US", {
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
            </p>

            {/* Actions */}
            {selected.status === "Pending" && (
              <div className="flex gap-3">
                <Button
                  onClick={() => handleApprove(selected.id)}
                  className="flex-1 bg-green-600 hover:bg-green-700 h-10"
                >
                  <Check className="w-4 h-4 mr-2" />
                  Approve Request
                </Button>
                <Button
                  onClick={() => handleReject(selected.id)}
                  variant="destructive"
                  className="flex-1 h-10"
                >
                  <X className="w-4 h-4 mr-2" />
                  Reject Request
                </Button>
              </div>
            )}
            {selected.status !== "Pending" && (
              <div className="flex items-center gap-2 p-4 bg-gray-100 rounded-xl text-sm text-gray-500">
                <span>This request has been {selected.status.toLowerCase()}.</span>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Select a request to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
