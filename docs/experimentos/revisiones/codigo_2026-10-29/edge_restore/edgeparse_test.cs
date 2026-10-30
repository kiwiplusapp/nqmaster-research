using System; using System.Collections.Generic; using System.Globalization;
class T {
		static bool EdgeParse(string[] p, out int d, out double sv, out int days, out bool alarm, out int fb, out bool warned, out List<string> off)
		{
			d = 0; sv = 0; days = 0; alarm = false; fb = 0; warned = false; off = new List<string>();
			if (p == null || p.Length < 9) return false;
			if (!int.TryParse(p[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out d) || !double.TryParse(p[2], NumberStyles.Any, CultureInfo.InvariantCulture, out sv)
				|| !int.TryParse(p[3], NumberStyles.Integer, CultureInfo.InvariantCulture, out days) || !int.TryParse(p[5], NumberStyles.Integer, CultureInfo.InvariantCulture, out fb)) return false;
			DateTime dt;
			if (d != 0 && !DateTime.TryParseExact(p[1], "yyyyMMdd", CultureInfo.InvariantCulture, DateTimeStyles.None, out dt)) return false;	// v3: no impossible dates (20260231)
			if (double.IsNaN(sv) || double.IsInfinity(sv) || sv < 0 || days < 0 || fb < 0) return false;	// v3: a NaN CUSUM would never alarm
			alarm = p[4] == "1"; warned = p[7] == "1";
			foreach (string x in p[6].Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries)) off.Add(x);
			return true;
		}

  static void Main() {
    string[] cases = { "Ultra;20261028;3.5;20;0;0;;0;2026-10-05;0.0899;26.93", "Ultra;0;0;0;0;0;;0;2026-10-05", "Ultra;20260231;3.5;20;0;0;;0;2026-10-05",
                       "Ultra;20261131;3.5;20;0;0;;0;2026-10-05", "Ultra;20261028;NaN;20;0;0;;0;2026-10-05", "Ultra;20261028;-1;20;0;0;;0;2026-10-05",
                       "Ultra;20261028;3.5;-2;0;0;;0;2026-10-05", "Ultra;20261028;3.5;20;1;250;REV06 MOM13;1;2026-10-05;0.0899;26.93" };
    foreach (string c in cases) { int d, days, fb; double sv; bool al, wn; List<string> off;
      Console.WriteLine("{0} -> {1}", c, EdgeParse(c.Split(';'), out d, out sv, out days, out al, out fb, out wn, out off)); }
  }
}