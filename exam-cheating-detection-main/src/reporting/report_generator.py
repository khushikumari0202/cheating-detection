import os
import pdfkit
from jinja2 import Environment, FileSystemLoader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import logging

class ReportGenerator:
    def __init__(self, config):
        self.config = config.get('reporting', {})
        self.output_dir = self.config.get('output_dir', './reports/generated')
        self.image_dir = os.path.join(self.output_dir, 'images')

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.template_env = Environment(loader=FileSystemLoader(template_path))

        self.logger = logging.getLogger('ReportGenerator')
        self.logger.setLevel(logging.INFO)

        self.severity_map = {
            'FACE_DISAPPEARED': 1,
            'GAZE_AWAY': 2,
            'MOUTH_MOVING': 3,
            'MULTIPLE_FACES': 4,
            'OBJECT_DETECTED': 5,
            'AUDIO_DETECTED': 3
        }

    def generate_report(self, student_info, violations, output_format='pdf'):
        try:
            output_format = str(output_format).lower()
            stats = self._calculate_stats(violations)
            stats['integrity_score'] = max(0, 100 - stats['severity_score'] * 5)

            timeline_image = self._generate_timeline(violations, student_info['id'])
            heatmap_image = self._generate_heatmap(violations, student_info['id'])

            report_data = {
                'student': student_info,
                'violations': violations,
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'stats': stats,
                'timeline_image': os.path.abspath(timeline_image) if timeline_image else None,
                'heatmap_image': os.path.abspath(heatmap_image) if heatmap_image else None,
                'has_images': bool(timeline_image or heatmap_image)
            }

            template = self.template_env.get_template('base_report.html')
            html_content = template.render(report_data)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{student_info['id']}_{timestamp}"
            output_path = os.path.join(self.output_dir, f"{filename}.{output_format}")

            if output_format == 'pdf':
                pdfkit_path = self.config.get(
                    'wkhtmltopdf_path',
                    r"C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"
                )
                if not os.path.exists(pdfkit_path):
                    self.logger.warning(f"wkhtmltopdf not found at {pdfkit_path}")
                pdfkit_config = pdfkit.configuration(wkhtmltopdf=pdfkit_path)
                pdfkit.from_string(html_content, output_path, configuration=pdfkit_config)
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)

            self.logger.info(f"Report generated at: {output_path}")
            return os.path.abspath(output_path)

        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            return None

    def _calculate_stats(self, violations):
        stats = {'total': len(violations), 'by_type': {}, 'timeline': [], 'severity_score': 0}
        for violation in violations:
            stats['by_type'][violation['type']] = stats['by_type'].get(violation['type'], 0) + 1
            stats['timeline'].append({
                'time': violation['timestamp'],
                'type': violation['type'],
                'severity': self.severity_map.get(violation['type'], 1)
            })
            stats['severity_score'] += self.severity_map.get(violation['type'], 1)
        stats['average_severity'] = stats['severity_score'] / stats['total'] if stats['total'] else 0
        return stats

    def _generate_timeline(self, violations, student_id):
        if not violations:
            return None
        try:
            times, severities, labels = [], [], []
            for v in violations:
                times.append(datetime.strptime(v['timestamp'], "%Y%m%d_%H%M%S_%f"))
                severities.append(self.severity_map.get(v['type'], 1))
                labels.append(v['type'])

            plt.figure(figsize=(12,5))
            plt.plot(times, severities, 'o-', markersize=8)
            for t, s, l in zip(times, severities, labels):
                plt.annotate(l, (t,s), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
            plt.title(f"Violation Timeline - {student_id}")
            plt.xlabel("Time")
            plt.ylabel("Severity Level")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            plt.tight_layout()

            path = os.path.join(self.image_dir, f"timeline_{student_id}.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            return path
        except Exception as e:
            self.logger.error(f"Failed to generate timeline: {str(e)}")
            return None

    def _generate_heatmap(self, violations, student_id):
        if not violations:
            return None
        try:
            counts = {}
            for v in violations:
                counts[v['type']] = counts.get(v['type'], 0) + 1
            if not counts:
                return None
            types, values = zip(*sorted(counts.items(), key=lambda x: x[1], reverse=True))

            plt.figure(figsize=(10,5))
            colors = [plt.cm.Reds(self.severity_map.get(t,1)/5) for t in types]
            bars = plt.barh(types, values, color=colors, edgecolor='black', linewidth=0.7)
            for bar in bars:
                plt.text(bar.get_width()+0.3, bar.get_y()+bar.get_height()/2, f"{int(bar.get_width())}", va='center', ha='left', fontsize=10)
            plt.title(f"Violation Frequency - {student_id}")
            plt.xlabel("Count")
            plt.ylabel("Violation Type")
            plt.grid(True, linestyle='--', alpha=0.3, axis='x')
            plt.tight_layout()

            path = os.path.join(self.image_dir, f"heatmap_{student_id}.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            return path
        except Exception as e:
            self.logger.error(f"Failed to generate heatmap: {str(e)}")
            return None
