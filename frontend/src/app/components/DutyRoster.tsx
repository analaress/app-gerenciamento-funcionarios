import { useState } from "react";
import { Clock, MapPin, Plus, ChevronLeft, ChevronRight } from "lucide-react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { rosterShifts } from "../data/mockData";

const SHIFT_TYPES = ["Morning", "Afternoon", "Night"] as const;

const shiftStyles: Record<string, { badge: string; row: string }> = {
  Morning: {
    badge: "bg-blue-50 text-blue-700 border-blue-200",
    row: "border-l-4 border-l-blue-400 bg-blue-50/40",
  },
  Afternoon: {
    badge: "bg-amber-50 text-amber-700 border-amber-200",
    row: "border-l-4 border-l-amber-400 bg-amber-50/40",
  },
  Night: {
    badge: "bg-purple-50 text-purple-700 border-purple-200",
    row: "border-l-4 border-l-purple-400 bg-purple-50/40",
  },
};

export function DutyRoster() {
  const allDates = Array.from(new Set(rosterShifts.map((s) => s.date))).sort();
  const [selectedDate, setSelectedDate] = useState("2026-04-01");
  const currentIndex = allDates.indexOf(selectedDate);

  const shiftsForDate = rosterShifts.filter((s) => s.date === selectedDate);

  const shiftGroups = SHIFT_TYPES.map((type) => ({
    type,
    shifts: shiftsForDate.filter((s) => s.shift === type),
  })).filter((g) => g.shifts.length > 0);

  const fmt = (d: string) =>
    new Date(d + "T12:00:00").toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });

  return (
    <div className="flex flex-col h-full">
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-5 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">Duty Roster</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {shiftsForDate.length} shift{shiftsForDate.length !== 1 ? "s" : ""} scheduled
          </p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Shift
        </Button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Date sidebar */}
        <div className="w-56 flex-shrink-0 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Select Date</p>
          </div>
          {allDates.map((date) => {
            const isActive = date === selectedDate;
            const count = rosterShifts.filter((s) => s.date === date).length;
            return (
              <button
                key={date}
                onClick={() => setSelectedDate(date)}
                className={`w-full text-left px-4 py-3.5 border-b border-gray-50 transition-colors ${
                  isActive ? "bg-blue-50 border-l-2 border-l-blue-500" : "hover:bg-gray-50"
                }`}
              >
                <p
                  className={`text-sm font-medium ${isActive ? "text-blue-700" : "text-gray-700"}`}
                >
                  {new Date(date + "T12:00:00").toLocaleDateString("en-US", {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                  })}
                </p>
                <p className={`text-xs mt-0.5 ${isActive ? "text-blue-500" : "text-gray-400"}`}>
                  {count} shift{count !== 1 ? "s" : ""}
                </p>
              </button>
            );
          })}
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-8">
          {/* Date navigation */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <button
                onClick={() => currentIndex > 0 && setSelectedDate(allDates[currentIndex - 1])}
                disabled={currentIndex === 0}
                className="p-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4 text-gray-600" />
              </button>
              <div>
                <h2 className="text-base font-semibold text-gray-900">{fmt(selectedDate)}</h2>
              </div>
              <button
                onClick={() =>
                  currentIndex < allDates.length - 1 &&
                  setSelectedDate(allDates[currentIndex + 1])
                }
                disabled={currentIndex === allDates.length - 1}
                className="p-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4 text-gray-600" />
              </button>
            </div>

            {/* Shift legend */}
            <div className="flex items-center gap-3">
              {SHIFT_TYPES.map((type) => (
                <Badge key={type} variant="outline" className={shiftStyles[type].badge}>
                  {type}
                </Badge>
              ))}
            </div>
          </div>

          {shiftsForDate.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-gray-400">
              <Clock className="w-12 h-12 mb-3 opacity-30" />
              <p className="text-sm">No shifts scheduled for this date</p>
              <Button className="mt-5 bg-blue-600 hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Add Shift
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              {shiftGroups.map(({ type, shifts }) => (
                <div key={type}>
                  <div className="flex items-center gap-3 mb-3">
                    <Badge variant="outline" className={shiftStyles[type].badge}>
                      {type} Shift
                    </Badge>
                    <span className="text-xs text-gray-400">
                      {shifts.length} staff · {shifts[0].startTime} – {shifts[0].endTime}
                    </span>
                  </div>

                  <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-100 bg-gray-50/60">
                          <th className="text-left px-5 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wide">Staff</th>
                          <th className="text-left px-5 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wide">Hours</th>
                          <th className="text-left px-5 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wide">Location</th>
                          <th className="text-left px-5 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wide">Shift</th>
                        </tr>
                      </thead>
                      <tbody>
                        {shifts.map((shift, idx) => (
                          <tr
                            key={shift.id}
                            className={`${shiftStyles[shift.shift].row} ${
                              idx < shifts.length - 1 ? "border-b border-gray-100" : ""
                            }`}
                          >
                            <td className="px-5 py-3.5">
                              <div className="flex items-center gap-3">
                                <div className="w-7 h-7 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                                  {shift.staffName.split(" ").map((n) => n[0]).join("")}
                                </div>
                                <span className="text-sm font-medium text-gray-900">{shift.staffName}</span>
                              </div>
                            </td>
                            <td className="px-5 py-3.5">
                              <div className="flex items-center gap-1.5 text-sm text-gray-600">
                                <Clock className="w-3.5 h-3.5 text-gray-400" />
                                {shift.startTime} – {shift.endTime}
                              </div>
                            </td>
                            <td className="px-5 py-3.5">
                              <div className="flex items-center gap-1.5 text-sm text-gray-600">
                                <MapPin className="w-3.5 h-3.5 text-gray-400" />
                                {shift.location}
                              </div>
                            </td>
                            <td className="px-5 py-3.5">
                              <Badge variant="outline" className={shiftStyles[shift.shift].badge}>
                                {shift.shift}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
