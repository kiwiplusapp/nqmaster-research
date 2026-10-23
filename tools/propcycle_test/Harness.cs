// Test harness for NQMaster.PropCycle (extracted between the <propcycle> markers by run_test.py). Reads paths.txt, writes out_cs.txt.
using System; using System.IO; using System.Globalization; using System.Collections.Generic;
namespace T {
public class H {
//PROPCYCLE//
	public static void Main(string[] a)
	{
		var ci = CultureInfo.InvariantCulture; var lines = File.ReadAllLines(a[0]); var o = new List<string>();
		int i = 0;
		while (i < lines.Length)
		{
			// header: case_id mode(eval|flex|pro|mffu) T D cons mind Q cap1 cap2 X npmax ndays nmin
			var h = lines[i++].Split(' '); string id = h[0], mode = h[1];
			var p = new PropCycle(); p.T = double.Parse(h[2], ci); p.D = double.Parse(h[3], ci); p.Cons = double.Parse(h[4], ci); p.MinDays = int.Parse(h[5]);
			p.Q = double.Parse(h[6], ci); p.Cap1 = double.Parse(h[7], ci); p.Cap2 = double.Parse(h[8], ci); p.X = double.Parse(h[9], ci); p.NpMax = int.Parse(h[10]);
			int nd = int.Parse(h[11]), nm = int.Parse(h[12]); p.Buf = p.D + 100;
			p.Model = mode == "flex" ? 0 : mode == "pro" ? 1 : 2;
			p.Start(mode != "eval");
			string res = id + " 0 " + nd + " 0 0"; double cash = 0; bool done = false;
			for (int d = 0; d < nd; d++)
			{
				var lo = lines[i++].Split(' '); var cl = lines[i++].Split(' ');
				if (done) continue;
				double raw0 = p.Raw, last = 0;
				for (int j = 0; j < nm; j++)
				{
					double l = double.Parse(lo[j], ci), c = double.Parse(cl[j], ci);
					int r = p.Bar(raw0 + Math.Min(l, c), raw0 + c);
					if (r != 0) { int day = r == 1 ? Math.Max(d, p.MinDays - 1) : d; res = id + " " + r + " " + day + " " + cash.ToString("0.00", ci) + " " + p.Pays; done = true; break; }
					last = c;
				}
				if (done) continue;
				double amt = p.DayClose(raw0 + last); cash += p.Split * amt;
				if (!p.Alive) { res = id + " 1 " + d + " " + cash.ToString("0.00", ci) + " " + p.Pays; done = true; }
			}
			if (!done) res = id + " 0 " + nd + " " + cash.ToString("0.00", ci) + " " + p.Pays;
			o.Add(res);
		}
		File.WriteAllLines(a[1], o.ToArray());
	}
}}
