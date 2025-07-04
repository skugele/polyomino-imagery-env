import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
from datetime import datetime
import zmq

LISTENER_PORT = 10001
HOST = "localhost"
TIMEOUT = 36000

def get_listener():
    context = zmq.Context()
    listener = context.socket(zmq.SUB)
    listener.setsockopt_string(zmq.SUBSCRIBE, "")
    listener.setsockopt(zmq.RCVTIMEO, TIMEOUT)  # Set a timeout of 36000 ms
    listener.connect(f"tcp://{HOST}:{LISTENER_PORT}")
    return listener

def receive(listener):
    poller = zmq.Poller()
    poller.register(listener, zmq.POLLIN)
    socks = dict(poller.poll(TIMEOUT))
    if listener in socks and socks[listener] == zmq.POLLIN:
        msg = listener.recv_string()
        ndx = msg.find('{')
        topic, encoded_payload = msg[0:ndx - 1], msg[ndx:]
        payload = json.loads(encoded_payload)
        return topic, payload
    raise zmq.Again("No message received within timeout")


""" Sample Responses
/polyomino/action_requested {'data': {'action': 'select_same_shape', 'seqno': 1}, 'header': {'seqno': 6, 'time': 1751298299749}}
/polyomino/selection-result/ {'data': {'result': True}, 'header': {'seqno': 7, 'time': 1751298299764}}
/polyomino-world/state {'data': {'last_action_seqno': 1, 'left_viewport': {'id': 17, 'screenshot': None, 'shape': 5}, 'playMode': True, 'right_viewport': {'id': 17, 'screenshot': None, 'shape': 5}, 'same': True, 'transformations': {'rotation_active': 321.97, 'scale': 0.83, 'translation': 10.27}}, 'header': {'seqno': 8, 'time': 1751298299783}}

"""
# metrics
'''
accuracy when same vs different
accuracy for each class
confusion matrix
'''


class PolyominoMetrics:
    def __init__(self):
        self.pending_actions = set()
        self.last_state = {
            'left_viewport': None,
            'right_viewport': None,
            'play_mode': None,
            'same': None,
            'transformations': None,
            'timestamp': None
        }
        self.performance_data = {
            'total_attempts': 0,
            'correct_answers': 0,
            'same_shape_attempts': 0,
            'same_shape_correct': 0,
            'different_shape_attempts': 0,
            'different_shape_correct': 0,
            'transformations': [],
            'results': [],
            'timestamps': []
        }
        
        self.points = []
        
        self.requested_actions = 0
        self.completed_actions = 0
    
    def process_action_request(self, payload):
        """Process incoming action request"""
        action = payload['data']['action']
        seqno = payload['data']['seqno']
        timestamp = payload['header']['time']
        
        print(f"Action requested: {action}, Seqno: {seqno}")
        self.pending_actions.add(seqno)
        self.requested_actions += 1
        
        # update total attempts if it's a selection action
        if "select_" in action:
            self.performance_data['total_attempts'] += 1
            if "same_shape" in action:
                self.performance_data['same_shape_attempts'] += 1
            elif "different_shape" in action:
                self.performance_data['different_shape_attempts'] += 1

    def process_selection_result(self, payload):
        """Process selection result"""
        result = payload['data']['result']
        seqno = payload['header']['seqno']
        timestamp = payload['header']['time']
        
        if result:
            self.performance_data['correct_answers'] += 1
            
        self.points.append((self.last_state['transformations']['rotation_active'],
                               self.last_state['transformations']['scale'],
                               self.last_state['transformations']['translation'],
                               result))
        
        if self.last_state['same'] is not None:
            if self.last_state['same']:
                if result:
                    self.performance_data['same_shape_correct'] += 1
                else:
                    print(f"Incorrect selection for same shape at seqno {seqno}")
            else:
                if not result:
                    self.performance_data['different_shape_correct'] += 1
                else:
                    print(f"Incorrect selection for different shape at seqno {seqno}")
    
    def process_last_state(self, payload):
        """Process game state update"""
        last_action_seqno = payload['data']['last_action_seqno']
        left_viewport = payload['data']['left_viewport']
        right_viewport = payload['data']['right_viewport']
        play_mode = payload['data']['playMode']
        same = payload['data']['same']
        transformations = payload['data']['transformations']
        timestamp = payload['header']['time']
        
        print(f"State update: Action {last_action_seqno}, Same: {same}, Transformations: {transformations}")
        
        if last_action_seqno in self.pending_actions:
            self.pending_actions.remove(last_action_seqno)
            self.completed_actions += 1
            print(f"Action {last_action_seqno} completed.")
        
        # Store state data
        state_data = {
            'seqno': last_action_seqno,
            'left_viewport': left_viewport,
            'right_viewport': right_viewport,
            'play_mode': play_mode,
            'same': same,
            'transformations': transformations,
            'timestamp': timestamp,
            'state_time': datetime.fromtimestamp(timestamp/1000)
        }
        self.last_state.update(state_data)

    
    def calculate_statistics(self):
        """Calculate comprehensive performance statistics"""
        data = self.performance_data
        
        if data['total_attempts'] == 0:
            return {
                'overall_accuracy': 0,
                'same_shape_accuracy': 0,
                'different_shape_accuracy': 0,
                'total_attempts': 0
            }
        
        overall_accuracy = (data['correct_answers'] / data['total_attempts']) * 100
        
        same_accuracy = 0
        if data['same_shape_attempts'] > 0:
            same_accuracy = (data['same_shape_correct'] / data['same_shape_attempts']) * 100
        
        different_accuracy = 0
        if data['different_shape_attempts'] > 0:
            different_accuracy = (data['different_shape_correct'] / data['different_shape_attempts']) * 100
        
        return {
            'overall_accuracy': overall_accuracy,
            'same_shape_accuracy': same_accuracy,
            'different_shape_accuracy': different_accuracy,
            'total_attempts': data['total_attempts'],
            'same_shape_attempts': data['same_shape_attempts'],
            'different_shape_attempts': data['different_shape_attempts'],
            'correct_answers': data['correct_answers'],
            'same_shape_correct': data['same_shape_correct'],
            'different_shape_correct': data['different_shape_correct']
        }
    
    def plot_3d_transformations(self, save_path=None):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        for (rotation, scale, translation, result) in self.points:
            color = 'green' if result else 'red'
            ax.scatter(rotation, scale, translation, c=color, alpha=0.5)

        ax.set_title('3D Transformations of Polyomino Shapes')
        ax.set_xlabel('Rotation (degrees)')
        ax.set_ylabel('Scale')
        ax.set_zlabel('Translation (units)')
        ax.grid(True)
        ax.legend(['Correct', 'Incorrect'])
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_performance_summary(self, save_path=None):
        """Plot performance summary statistics"""
        stats = self.calculate_statistics()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Overall accuracy pie chart
        correct = stats['correct_answers']
        incorrect = stats['total_attempts'] - correct
        ax1.pie([correct, incorrect], labels=['Correct', 'Incorrect'], 
                colors=['green', 'red'], autopct='%1.1f%%', startangle=90)
        ax1.set_title(f'Overall Accuracy: {stats["overall_accuracy"]:.1f}%')
        
        # Same vs Different accuracy bar chart
        categories = ['Same Shape', 'Different Shape']
        accuracies = [stats['same_shape_accuracy'], stats['different_shape_accuracy']]
        bars = ax2.bar(categories, accuracies, color=['blue', 'orange'])
        ax2.set_ylabel('Accuracy (%)')
        ax2.set_title('Accuracy by Shape Comparison Type')
        ax2.set_ylim(0, 100)
        
        # Add value labels on bars
        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{acc:.1f}%', ha='center', va='bottom')
        
        # Attempts distribution
        same_attempts = stats['same_shape_attempts']
        diff_attempts = stats['different_shape_attempts']
        ax3.bar(['Same Shape', 'Different Shape'], [same_attempts, diff_attempts], 
                color=['lightblue', 'orange'])
        ax3.set_ylabel('Number of Attempts')
        ax3.set_title('Distribution of Attempts')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def print_detailed_report(self):
        """Print a detailed performance report"""
        stats = self.calculate_statistics()
        
        print("\n" + "="*50)
        print("POLYOMINO PERFORMANCE REPORT")
        print("="*50)
        print(f"Total Attempts: {stats['total_attempts']}")
        print(f"Overall Accuracy: {stats['overall_accuracy']:.2f}%")
        print(f"Correct Answers: {stats['correct_answers']}")
        print("\n" + "-"*30)
        print("BREAKDOWN BY SHAPE COMPARISON:")
        print("-"*30)
        print(f"Same Shape Attempts: {stats['same_shape_attempts']}")
        print(f"Same Shape Correct: {stats['same_shape_correct']}")
        print(f"Same Shape Accuracy: {stats['same_shape_accuracy']:.2f}%")
        print()
        print(f"Different Shape Attempts: {stats['different_shape_attempts']}")
        print(f"Different Shape Correct: {stats['different_shape_correct']}")
        print(f"Different Shape Accuracy: {stats['different_shape_accuracy']:.2f}%")
        print("\n" + "-"*30)


def main():
    metrics = PolyominoMetrics()
    listener = get_listener()
    
    try:
        while True:
            topic, payload = receive(listener)
            
            if "action_requested" in topic:
                metrics.process_action_request(payload)
                
            elif "selection-result" in topic:
                metrics.process_selection_result(payload)
                
            elif "state" in topic:
                metrics.process_last_state(payload)
                
                # Print periodic updates
                if metrics.performance_data['total_attempts'] > 0 and \
                   metrics.performance_data['total_attempts'] % 10 == 0:
                    print(f"\n--- Performance Update (After {metrics.performance_data['total_attempts']} attempts) ---")
                    stats = metrics.calculate_statistics()
                    print(f"Current Accuracy: {stats['overall_accuracy']:.2f}%")
                    print(f"Same Shape Accuracy: {stats['same_shape_accuracy']:.2f}%")
                    print(f"Different Shape Accuracy: {stats['different_shape_accuracy']:.2f}%")
                    print("-" * 50)
    
    except KeyboardInterrupt:
        metrics.print_detailed_report()
        
        # Create visualizations
        if metrics.performance_data['total_attempts'] > 0:
            print("Creating performance visualizations...")
            metrics.plot_performance_summary(save_path="performance_summary.png")
            metrics.plot_3d_transformations(save_path="3d_transformations.png")

if __name__ == "__main__":
    main()