import { useState } from "react";
import { DollarSign, Search, Mail, Phone, TrendingUp, Users } from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { staffList } from "../data/mockData";

const deptColors: Record<string, string> = {
  Engineering: "bg-blue-50 text-blue-700 border-blue-200",
  Product: "bg-purple-50 text-purple-700 border-purple-200",
  Design: "bg-pink-50 text-pink-700 border-pink-200",
  Marketing: "bg-amber-50 text-amber-700 border-amber-200",
  "Human Resources": "bg-green-50 text-green-700 border-green-200",
  Sales: "bg-indigo-50 text-indigo-700 border-indigo-200",
};

export function Payroll() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string>(staffList[0].id);

  const filteredStaff = staffList.filter(
    (s) =>
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.department.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalPayroll = staffList.reduce((sum, s) => sum + s.salary, 0);
  const avgSalary = Math.round(totalPayroll / staffList.length);
  const maxSalary = Math.max(...staffList.map((s) => s.salary));

  const selected = staffList.find((s) => s.id === selectedId);

  return (
    <div className="flex flex-col h-full">
      {/* Top stats bar */}
      <div className="bg-white border-b border-gray-200 px-8 py-5 flex items-center gap-8 flex-shrink-0">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">Payroll</h1>
        </div>
        <div className="h-8 w-px bg-gray-200" />
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-green-100 rounded-lg">
            <DollarSign className="w-4 h-4 text-green-600" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Total Monthly</p>
            <p className="text-sm font-bold text-gray-900">${(totalPayroll / 12 / 1000).toFixed(1)}K</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-100 rounded-lg">
            <TrendingUp className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Avg Salary</p>
            <p className="text-sm font-bold text-gray-900">${(avgSalary / 1000).toFixed(1)}K</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-purple-100 rounded-lg">
            <Users className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Total Staff</p>
            <p className="text-sm font-bold text-gray-900">{staffList.length}</p>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Staff list */}
        <div className="w-80 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
          {/* Search */}
          <div className="px-4 py-3 border-b border-gray-100">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search staff..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-gray-50 border-gray-200 h-9 text-sm"
              />
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto">
            {filteredStaff.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <Search className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p className="text-sm">No staff found</p>
              </div>
            ) : (
              filteredStaff.map((staff) => (
                <button
                  key={staff.id}
                  onClick={() => setSelectedId(staff.id)}
                  className={`w-full text-left px-5 py-3.5 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                    selectedId === staff.id ? "bg-blue-50 border-l-2 border-l-blue-500" : ""
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                      {staff.name.split(" ").map((n) => n[0]).join("")}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{staff.name}</p>
                      <p className="text-xs text-gray-400 truncate">{staff.role}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-sm font-semibold text-gray-800">
                        ${(staff.salary / 1000).toFixed(0)}K
                      </p>
                      <p className="text-xs text-gray-400">/ yr</p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Detail panel */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-8">
          {selected ? (
            <div className="max-w-2xl space-y-6">
              {/* Profile header */}
              <div className="bg-white rounded-2xl border border-gray-200 p-6">
                <div className="flex items-start gap-5">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center text-white text-xl font-bold flex-shrink-0">
                    {selected.name.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <div className="flex-1">
                    <h2 className="text-xl font-semibold text-gray-900">{selected.name}</h2>
                    <p className="text-gray-500 mt-0.5">{selected.role}</p>
                    <Badge variant="outline" className={`mt-2 ${deptColors[selected.department] ?? "bg-gray-50 text-gray-700 border-gray-200"}`}>
                      {selected.department}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-gray-900">
                      ${(selected.salary / 1000).toFixed(0)}K
                    </p>
                    <p className="text-sm text-gray-400">Annual salary</p>
                  </div>
                </div>
              </div>

              {/* Salary breakdown */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
                    Salary Breakdown
                  </h3>
                  <div className="space-y-3">
                    {[
                      { label: "Annual", value: selected.salary },
                      { label: "Monthly", value: Math.round(selected.salary / 12) },
                      { label: "Bi-weekly", value: Math.round(selected.salary / 26) },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                        <span className="text-sm text-gray-500">{label}</span>
                        <span className="text-base font-semibold text-gray-900">
                          ${value.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Salary vs max bar */}
                  <div className="mt-5 pt-4 border-t border-gray-100">
                    <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                      <span>vs highest earner</span>
                      <span>{Math.round((selected.salary / maxSalary) * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(selected.salary / maxSalary) * 100}%` }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Contact */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
                    Contact Information
                  </h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      <Mail className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-400">Email</p>
                        <p className="text-sm text-gray-800">{selected.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      <Phone className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-400">Phone</p>
                        <p className="text-sm text-gray-800">{selected.phone}</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Actions */}
              <div className="flex gap-3">
                <Button className="flex-1 bg-blue-600 hover:bg-blue-700 h-10">
                  <DollarSign className="w-4 h-4 mr-2" />
                  Process Payment
                </Button>
                <Button variant="outline" className="flex-1 h-10">
                  View Payment History
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select a staff member to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
